from __future__ import annotations
import io
import math
from pathlib import Path
import re
from typing import Optional, TextIO, Union, overload

import adsk.cam

from .line import Line
from .settings import Settings
from .operations import Operations
from ...lib.fusionAddInUtils.general_utils import Utils

class Setup(Line):
    def __init__(self, setup: adsk.cam.Setup, index: int, markSelected: bool = False):
        self._setup = setup
        self._index = index
        self._isSelected = False if self._setup is None else markSelected or self._setup.isSelected
        self._outputFilename = None
        self._operations = None 
        self.outputFilePath = ""
        self._origin: adsk.core.Point3D = None
        self._headerGenerated = False

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
        if self._operations is None:
            return False
        return self._operations.hasTail

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
        from .programs import Programs

        # Time to parse the operations of this setup unless it isn't suppressed.
        self._operations = None if \
                self.isSuppressed \
                and not self.isSelected \
            else Operations(list(operation for operation in self._setup.allOperations))

        if self._operations is None:
            return # Don't process this setup.

        # Don't spam the user with temporary files that will be deleted anyway
        Programs.Current.DisableOpenInEditor()

        # Make sure that the setup has all its toolpaths generated
        Programs.CheckAndGenerateToolpath(self._setup)

        self._operations.Parse(tmpPath)

    def SetOutputFileName(self, fileName):
        self._outputFileName = fileName

    def WriteSetupName(self, fileHandler: TextIO, lineNumber: int) -> int:
        return Setup._writeLine(fileHandler, f"({self._setup.name})", lineNumber)

    def WriteHeaderStart(self, fileHandler: TextIO, lineNumber: int) -> int:
        return self._operations.WriteHeaderStart(fileHandler, lineNumber)

    def WriteToolComment(self, fileHandler: TextIO, lineNumber: int) -> int:
        return self._operations.WriteToolComment(fileHandler, lineNumber)
    
    def WriteHeaderEnd(self, fileHandler: TextIO, lineNumber: int) -> int:
        return self._operations.WriteHeaderEnd(fileHandler, lineNumber)

    #region GenerateBody
    # Type signatures for tools (mypy/IDE) hints

    # If GenerateBody is called with a fileHandler it means that the output
    # will only be one file
    @overload
    def WriteBody(self, fileHandler: TextIO, lineNumber: int, *, rotationAngle: Optional[float] = None, preserveRotation: Optional[bool] = False) -> int: ...

    # If GenerateBody is called with folder it means that 
    # multiple files will be generated on lower levels of the hierarchy
    @overload
    def WriteBody(self, folderPath: Path, lineNumber: int, fileName: str, fileExtension: str, *, rotationAngle: Optional[float] = None, preserveRotation: Optional[bool] = False) -> int: ...

    # Runtime implementation of Generate
    def WriteBody(self, pathOrFile, lineNumber: int, fileName: Optional[str] = None, fileExtension: Optional[str] = None, *, rotationAngle: Optional[float] = None, preserveRotation: Optional[bool] = False) -> int:

        # case 1: given an open file (TextIO) means that everything 
        # should be written to it and no directory structure
        # should be created.
        if isinstance(pathOrFile, io.TextIOBase):
            fileHandler: TextIO = pathOrFile
            return self._operations.WriteBody(fileHandler, lineNumber, rotationAngle = rotationAngle, preserveRotation=preserveRotation)
        
        # case 2: given folder there is a structure to create
        if isinstance(pathOrFile, Path):
            # This is probably a good place to split on tool change..?
            return self._operations.WriteBody(pathOrFile, lineNumber, fileName, fileExtension, rotationAngle = rotationAngle, preserveRotation=preserveRotation)
        raise TypeError("Call GenerateBody(fileHandler) or GenerateBody(folderPath, fileName, fileExtension)")
    #endregion

    #region GenerateTail 

    @property
    def hasTail(self):
        return self._operations is not None and self._operations.hasTail
    
    # Type signatures for tools (mypy/IDE) hints

    # If GenerateTail is called with a fileHandler it means that the output
    # will only be one file
    @overload
    def WriteTail(self, fileHandler: TextIO) -> int: ...

    # If GenerateTail is called with folder it means that 
    # multiple files will be generated on lower levels of the hierarchy
    @overload
    def WriteTail(self, folderPath: Path, fileName: str, fileExtension: str) -> int: ...

    # Runtime implementation of GenerateTail
    def WriteTail(self, arg, lineNumber: int, fileName: Optional[str] = None, fileExtension: Optional[str] = None) -> int:

        # case 1: given an open file (TextIO) means that everything 
        # should be written to it and no directory structure
        # should be created.

        if isinstance(arg, io.TextIOBase) and fileName is None and fileExtension is None:
            fileHandler: TextIO = arg
            if not self._operations.hasTail:
                return lineNumber
            return self._operations.WriteTail(fileHandler, lineNumber)
                
        # case 2: given folder + name + ext
        elif isinstance(arg, Path) and fileName is not None and fileExtension is not None:
            # This is probably a good place to split on tool change..?
            if not self._operations.hasTail:
                return lineNumber
            return self._operations.WriteTail(arg, lineNumber, fileName, fileExtension)
        else:
            raise TypeError("Call GenerateTail(fileHandler) or GenerateTail(folderPath, fileName, fileExtension)")  
    #endregion

    def WriteOperations(self, folderPath: Path, fileName: str, fileExtension: str, *, rotationAngle: Optional[float] = None, preserveRotation: Optional[bool] = False) -> int:
        if Settings(Settings.FLAT_FILE_STRUCTURE):
            fileName = ("{fileName}_{setupName}" if Settings(Settings.FLAT_FILE_STRUCTURE) else "{setupName}") \
                .format(
                    fileName = fileName, 
                    setupName = Utils.sanitizeFilename(self.name, preserveExtension = False))
            folder = folderPath 
        else:
            folder = folderPath / Utils.sanitizeFilename(self.name, preserveExtension = False)
        folder.mkdir(parents=True, exist_ok=True)
        return self._operations.WriteOperations(folder, fileName, fileExtension, rotationAngle = rotationAngle, preserveRotation = preserveRotation)
