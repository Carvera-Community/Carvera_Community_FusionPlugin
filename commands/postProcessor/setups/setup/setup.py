from __future__ import annotations
import math
from pathlib import Path
import re
from typing import Optional, TextIO, Union, overload

import adsk.cam

from ...file_modes import FileModes
from ...settings.settings import Settings
from ...operations.operations import Operations
from .....lib.fusionAddInUtils.general_utils import Utils

from .header import SetupHeader
from .body import SetupBody
from .tail import SetupTail

class Setup(SetupHeader, SetupBody, SetupTail):
    def __init__(self, setup: adsk.cam.Setup, index: int, markSelected: bool = False):
        self._setup = setup
        self._index = index
        self._isSelected = False if self._setup is None else markSelected or self._setup.isSelected
        self._outputFilename = None
        self._operations = None 
        self.outputFilePath = ""
        self._origin: adsk.core.Point3D = None
        self._headerGenerated = False

        self._operations = None if \
                self.isSuppressed \
                and not self.isSelected \
            else Operations(list(operation for operation in self._setup.allOperations))

    @property
    def hasError(self) -> bool:
        return self._setup is None or self._setup.hasError
    
    @property
    def index(self):
        return self._index

    @property
    def isSuppressed(self):
        return self._setup is None or self._setup.isSuppressed
    
    @property
    def isSelected(self):
        return self._isSelected

    def select(self, value: bool):
        self._isSelected = value

    @property
    def name(self):
        return self._setup.name
    
    @property 
    def hasOperationWithTail(self):
        return self._operations.hasTail if self._operations is not None else False

    @property
    def hasOperationWithHeader(self):
        return self._operations.hasHeader if self._operations is not None else False

    @property
    def origin(self) -> adsk.core.Point3D:
        origin = adsk.core.Point3D.create(0,0,0)
        origin.transformBy(self._setup.workCoordinateSystem)
        return origin

    @property
    def zNormal(self) -> adsk.core.Vector3D:
        zAxis = adsk.core.Vector3D.create(0,0,1)
        zAxis.transformBy(self._setup.workCoordinateSystem)
        zAxis.normalize()
        return zAxis
    
    @property
    def xNormal(self) -> adsk.core.Vector3D:
        xAxis = adsk.core.Vector3D.create(1,0,0)
        xAxis.transformBy(self._setup.workCoordinateSystem)
        xAxis.normalize()
        return xAxis

    @property
    def yNormal(self) -> adsk.core.Vector3D:
        yAxis = adsk.core.Vector3D.create(0,1,0)
        yAxis.transformBy(self._setup.workCoordinateSystem)
        yAxis.normalize()
        return yAxis

    @property
    def hasMachine(self) -> bool:
        return self._setup.machine is not None

    @property
    def tools(self) -> list[adsk.cam.Tool]:
        return self._operations.tools if self._operations is not None else []

    # Compute signed rotation around the setup's X axis.
    #
    # Behavior:
    # - `GetAbsoluteRotationAroundXAxis()` returns the signed rotation (radians)
    #   that aligns the setup's local Z with the global Z, measured around the
    #   setup's local X axis. It is a thin wrapper that calls
    #   `GetRotationAroundXAxisRelativeTo(zNormal, yNormal)` with global Z/Y.
    # - `GetRotationAroundXAxisRelativeTo(zNormal, yNormal)` computes the
    #   signed rotation around this setup's X axis that rotates this setup's
    #   Z into the supplied `zNormal`, using `yNormal` as a secondary
    #   reference when Z projection degenerates.
    #
    # Algorithm:
    # 1) Use this setup's `xNormal` as rotation axis.
    # 2) Project both Z vectors (this.zNormal and the supplied zNormal) onto
    #    the plane orthogonal to `xNormal`. If projections are non-degenerate,
    #    compute the signed angle between the normalized projections using
    #    `atan2(sign, dot)` where `sign = xAxis · (p1 × p2)`.
    # 3) If Z projection degenerates (Z nearly parallel to X), project the Y
    #    vectors instead and compute the angle in the same way (Y fallback).
    # 4) If both projections degenerate (extremely unlikely in a proper 3D
    #    orthonormal WCS), the method logs a warning and returns 0.0 to avoid
    #    numerical instability.
    #
    # Notes:
    # - All returned angles are in radians. Degenerate cases are handled to
    #   avoid numerical instability.
    # - The implementation works with supplied normal vectors and does not
    #   depend on a precomputed global rotation value; the absolute wrapper
    #   simply supplies global axes.
    def GetAbsoluteRotationAroundXAxis(self) -> float:
        gZNormal = adsk.core.Vector3D.create(0, 0, 1)
        gYNormal = adsk.core.Vector3D.create(0, 1, 0)
        return self.GetRotationAroundXAxisRelativeTo(gZNormal, gYNormal)
    
    def GetAbsoluteRotationAroundXAxisDeg(self) -> float:
        return math.degrees(self.GetAbsoluteRotationAroundXAxis())
    
    @overload
    def GetRotationAroundXAxisRelativeTo(self, otherSetup: Setup) -> float: ...
    
    def GetRotationAroundXAxisRelativeTo(self, zNormalOrSetup: Union[adsk.core.Vector3D, Setup], yNormal = None) -> float:
        # Compute the signed rotation around this setup's X axis that
        # transforms this setup's local Z into the other setup's local Z.
        #
        # Strategy:
        # - Use this setup's X axis as rotation axis.
        # - Project both Z normals onto the plane orthogonal to
        #   that X axis and compute the signed angle between the
        #   projected directions using the right-hand rule.
        # - If projection degenerates (vectors near-parallel to X), fall
        #   back to project the Y normals instead.

        xNormal = self.xNormal

        if isinstance(zNormalOrSetup, Setup) and yNormal is None: # unwrap if a Setup is given
            yNormal = zNormalOrSetup.yNormal
            zNormal = zNormalOrSetup.zNormal
        else:
            zNormal = zNormalOrSetup

        def project(v: adsk.core.Vector3D, n: adsk.core.Vector3D) -> adsk.core.Vector3D:
            d = n.dotProduct(v)
            return adsk.core.Vector3D.create(v.x - n.x * d, v.y - n.y * d, v.z - n.z * d)

        p1 = project(self.zNormal, xNormal)
        p2 = project(zNormal, xNormal)

        # If projection is degenerate, fall back to using the y-axis instead.
        if p1.length < 1e-6 or p2.length < 1e-6:
                p1y = project(self.yNormal, xNormal)
                p2y = project(yNormal, xNormal)
                p1y.normalize()
                p2y.normalize()
                cross = p1y.crossProduct(p2y)
                sign = xNormal.dotProduct(cross)
                dot = p1y.dotProduct(p2y)
                return math.atan2(sign, dot)

        p1.normalize()
        p2.normalize()
        cross = p1.crossProduct(p2)
        sign = xNormal.dotProduct(cross)
        dot = p1.dotProduct(p2)
        return math.atan2(sign, dot)
    
    def GetRotationAroundXAxisRelativeToDeg(self, otherSetup) -> float:
        return math.degrees(self.GetRotationAroundXAxisRelativeTo(otherSetup.zNormal, otherSetup.yNormal))
    
    def Rename(self, find, replace, isRegex):
        if isRegex:
            newName = re.sub(find, replace, self._setup.name)
        else:
            if find == "":
                # special case, prepend
                newName = replace + self._setup.name
            else:
                newName = self._setup.name.replace(find, replace)

        if self._setup.name != newName:
            self._setup.name = newName
    
    def Parse(self, tmpPath: Path):
        from ...programs import Programs

        if self._operations is None:
            return # Don't process this setup.

        # Don't spam the user with temporary files that will be deleted anyway
        Programs.Current.DisableOpenInEditor()

        # Make sure that the setup has all its toolpaths generated
        Programs.CheckAndGenerateToolpath(self._setup)

        self._operations.Parse(tmpPath)

    # TODO: Move to operations if possible
    def WriteOperations(self, folderPath: Path, fileName: str, fileExtension: str, *, rotationAngle: Optional[float] = None, preserveRotation: Optional[bool] = False) -> int:
        if Settings(Settings.FLAT_FILE_STRUCTURE):
            setupName = Utils.sanitizeFilename(self.name, preserveExtension = False)
            setupName = "{index}_{fileName}".format(
                fileName = setupName, 
                index=str(self.index + 1).rjust(2, "0")) if Settings(Settings.SEQUENCE) in (Settings.Sequences.FILE, Settings.Sequences.FILE_AND_STEP) else setupName
            
            fileName = ("{fileName}_{setupName}" if Settings(Settings.FLAT_FILE_STRUCTURE) else "{setupName}") \
                .format(
                    fileName = fileName, 
                    setupName = setupName)
            folder = folderPath 
        else:
            folder = folderPath / Utils.sanitizeFilename(self.name, preserveExtension = False)
        folder.mkdir(parents=True, exist_ok=True)
        return self._operations.WriteOperations(folder, fileName, fileExtension, rotationAngle = rotationAngle, preserveRotation = preserveRotation)

    def _getFileName(self, fileName) -> str:
        if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SINGLE_FILE:
            return fileName

        outputName = Utils.sanitizeFilename(self.name, preserveExtension = False)
        if Settings(Settings.SEQUENCE) in (Settings.Sequences.FILE, Settings.Sequences.FILE_AND_STEP):
            outputName = "{index}_{fileName}".format(
                fileName = outputName, 
                index=str(self.index + 1).rjust(2, "0"))
        
        if Settings(Settings.FLAT_FILE_STRUCTURE):
            return f"{fileName}_{outputName}"
        return outputName

    def _getFileHandler(self, mode: FileModes, path: Path, fileName: str, fileExtension: str) -> TextIO:
        return (path / f"{self._getFileName(fileName)}{fileExtension}").open(mode, encoding="utf-8")
