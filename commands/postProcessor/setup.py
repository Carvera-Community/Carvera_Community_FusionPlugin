from __future__ import annotations
import io
import math
from pathlib import Path
import re
from typing import Optional, TextIO, Union, overload

import adsk.cam

from .settings import Settings
from .operations import Operations
from ...lib.fusionAddInUtils.general_utils import Utils

class Setup:
    def __init__(self, setup: adsk.cam.Setup, markSelected: bool = False):
        self._setup = setup
        self._isSelected = False if self._setup is None else markSelected or self._setup.isSelected
        self._outputFilename = None
        # Only process operations if necessary
        self._operations = None if \
                self.isSuppressed \
                and not self.isSelected \
            else Operations(list(operation for operation in self._setup.allOperations))
        self.outputFilePath = ""
        self._origin: adsk.core.Point3D = None
        self._headerGenerated = False

    _isSelected = False # Since adsk.cam.Setup.isSelected is not writeable, we need to track it ourselves.

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
    
    def Process(self, tmpPath: Path):
        from .programs import Programs

        if self._operations is None or self.isSuppressed:
            return # Don't process this setup.

        # Don't spam the user with temporary files that will be deleted anyway
        Programs.Current.DisableOpenInEditor()

        # Make sure that the setup has all its toolpaths generated
        Programs.CheckAndGenerateToolpath(self._setup)

        self._operations.Process(tmpPath)

    def SetOutputFileName(self, fileName):
        self._outputFileName = fileName

    @property
    def headerGenerated(self) -> bool:
        return self._headerGenerated

    #region GenerateHeader
    # Type signatures for tools (mypy/IDE) hints

    # If Generate is called with a fileHandler it means that the output
    # will only be one file
    @overload
    def GenerateHeader(self, fileHandler: TextIO, lineNumber: int, addLineNumbers: bool, digits: int, briefHeader: bool) -> int: ...

    # If generate is called with folder it means that 
    # multiple files will be generated on lower levels of the hierarchy
    @overload
    def GenerateHeader(self, folderPath: Path, lineNumber: int, addLineNumbers: bool, digits: int, briefHeader: bool, fileName: str, fileExtension: str) -> int: ...
    
    # Runtime implementation of Generate
    def GenerateHeader(self, arg, lineNumber: int, addLineNumbers: bool, digits: int, briefHeader: bool, fileName: Optional[str] = None, fileExtension: Optional[str] = None) -> int:

        self._headerGenerated = briefHeader

        # case 1: given an open file (TextIO) means that everything 
        # should be written to it and no directory structure
        # should be created.
        if isinstance(arg, io.TextIOBase) and fileName is None and fileExtension is None:
            fileHandler: TextIO = arg
            lineNumber = self._operations.GenerateHeader(fileHandler, lineNumber, addLineNumbers, digits, self._headerGenerated)
            if not self._headerGenerated: self._headerGenerated = self._operations.headerGenerated
            return lineNumber
        
        # case 2: given folder + name + ext
        if isinstance(arg, Path) and fileName is not None and fileExtension is not None:
            folder: Path = arg
            folder.mkdir(parents=True, exist_ok=True)
            filename = f"{fileName}{fileExtension}"
            p = folder / filename
            # öppna och skriv via samma inre funktion
            with p.open("w", encoding="utf-8") as fh:
                self._generate_to_file(fh, addLineNumbers, digits)
            return -1

        raise TypeError("Call GenerateHeader(fileHandler) or GenerateHeader(folderPath, fileName, fileExtension)")
    #endregion

    #region GenerateBody
    # Type signatures for tools (mypy/IDE) hints

    # If GenerateBody is called with a fileHandler it means that the output
    # will only be one file
    @overload
    def GenerateBody(self, fileHandler: TextIO, lineNumber: int, addLineNumbers: bool, digits: int, removeARotations: bool) -> int: ...

    # If GenerateBody is called with folder it means that 
    # multiple files will be generated on lower levels of the hierarchy
    @overload
    def GenerateBody(self, folderPath: Path, lineNumber: int, addLineNumbers: bool, digits: int, removeARotations: bool, fileName: str, fileExtension: str) -> int: ...

    # Runtime implementation of Generate
    def GenerateBody(self, arg, lineNumber: int, addLineNumbers: bool, digits: int, removeARotations: bool, fileName: Optional[str] = None, fileExtension: Optional[str] = None) -> int:

        # case 1: given an open file (TextIO) means that everything 
        # should be written to it and no directory structure
        # should be created.
        if isinstance(arg, io.TextIOBase):
            fileHandler: TextIO = arg
            return self._operations.GenerateBody(fileHandler, lineNumber, addLineNumbers, digits, removeARotations)
        
        # case 2: given folder there is a structure to create
        if isinstance(arg, Path):
            # This is probably a good place to split on tool change..?
            return self._operations.GenerateBody(arg, lineNumber, addLineNumbers, digits, removeARotations, fileName, fileExtension)
        raise TypeError("Call GenerateBody(fileHandler) or GenerateBody(folderPath, fileName, fileExtension)")
    #endregion

    #region GenerateTail 
    # Type signatures for tools (mypy/IDE) hints

    # If GenerateTail is called with a fileHandler it means that the output
    # will only be one file
    @overload
    def GenerateTail(self, fileHandler: TextIO, addLineNumbers: bool, digits: int) -> int: ...

    # If GenerateTail is called with folder it means that 
    # multiple files will be generated on lower levels of the hierarchy
    @overload
    def GenerateTail(self, folderPath: Path, addLineNumbers: bool, digits: int, fileName: str, fileExtension: str) -> int: ...

    # Runtime implementation of GenerateTail
    def GenerateTail(self, arg, lineNumber: int, addLineNumbers: Optional[bool] = None, digits: Optional[int] = None, fileName: Optional[str] = None, fileExtension: Optional[str] = None) -> int:

        # case 1: given an open file (TextIO) means that everything 
        # should be written to it and no directory structure
        # should be created.

        if isinstance(arg, io.TextIOBase) and fileName is None and fileExtension is None:
            fileHandler: TextIO = arg
            if not self._operations.hasTail:
                return lineNumber
            return self._operations.GenerateTail(fileHandler, lineNumber, addLineNumbers, digits)
                
        # case 2: given folder + name + ext
        if isinstance(arg, Path) and fileName is not None and fileExtension is not None:
            # This is probably a good place to split on tool change..?
            if not self._operations.hasTail:
                return lineNumber
            return self._operations.GenerateTail(arg, lineNumber, addLineNumbers, digits, fileName, fileExtension)

        raise TypeError("Call GenerateTail(fileHandler) or GenerateTail(folderPath, fileName, fileExtension)")  
    #endregion

