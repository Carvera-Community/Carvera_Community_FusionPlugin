from __future__ import annotations

import math
from pathlib import Path
import re

from typing import (
    Iterator,
    Optional, 
    Union
)

from adsk.cam import (
    Setup as adskSetup,
    Operation as adskOperation,
    Tool as adskTool
)
from adsk.core import (
    Point3D,
    Vector3D
)
from ...operations.operations_context import OperationsContext
from .setup_context import SetupContext

from ...operations.operations import Operations

from .header_writer import (
    writeHeader,
    writeHeaderStart,
    writeToolComments,
    writeHeaderEnd
)
from .body_writer import writeBody
from .tail_writer import writeTail

class Setup():
    def __init__(self, ctx: SetupContext, setup: adskSetup, index: int, isDefaultSelected: bool = False):
        self.ctx = ctx
        ctx.setup = setup
        ctx.index = index
        ctx.isSelected = isDefaultSelected

    @property
    def index(self) -> int:
        return self.ctx.index
    
    @property
    def isSelected(self) -> bool:
        return self.ctx.isSelected

    def Select(self, value: bool):
        self.ctx.isSelected = value

    @property
    def name(self) -> str:
        return self.ctx.setup.name
    
    @property
    def hasOperationWithHeader(self) -> bool:
        return self.ctx.operations.hasHeader if self.ctx.operations is not None else False

    @property
    def origin(self) -> Point3D:
        origin = Point3D.create(0,0,0)
        origin.transformBy(self.ctx.setup.workCoordinateSystem)
        return origin

    @property
    def zNormal(self) -> Vector3D:
        zAxis = Vector3D.create(0,0,1)
        zAxis.transformBy(self.ctx.setup.workCoordinateSystem)
        zAxis.normalize()
        return zAxis
    
    @property
    def xNormal(self) -> Vector3D:
        xAxis = Vector3D.create(1,0,0)
        xAxis.transformBy(self.ctx.setup.workCoordinateSystem)
        xAxis.normalize()
        return xAxis

    @property
    def yNormal(self) -> Vector3D:
        yAxis = Vector3D.create(0,1,0)
        yAxis.transformBy(self.ctx.setup.workCoordinateSystem)
        yAxis.normalize()
        return yAxis

    @property
    def hasMachine(self) -> bool:
        return self.ctx.setup.machine is not None

    # As the operations aren't loaded until parse is called the tools
    # is read dynamically from the adsk object directly.
    def getTools(self) -> Iterator[adskTool]:
        for x in self.ctx.setup.allOperations:
            operation = adskOperation.cast(x)
            if operation.isValid and not operation.hasError:
                yield operation.tool

    def SetOutputPath(self, path: Path):
        path.mkdir(parents=True, exist_ok=True)
        if self.ctx.operations is not None:
            self.ctx.operations.SetOutputPath(path)

    def SetFileExtension(self, fileExtension: str):
        if self.ctx.operations is not None:
            self.ctx.operations.SetFileExtension(fileExtension)

    #region Compute signed rotation around the setup's X axis.
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
    #endregion

    def GetAbsoluteRotationAroundXAxis(self) -> float:
        gZNormal = Vector3D.create(0, 0, 1)
        gYNormal = Vector3D.create(0, 1, 0)
        return self.GetRotationAroundXAxisRelativeTo(gZNormal, gYNormal)
    
    def GetAbsoluteRotationAroundXAxisDeg(self) -> float:
        return math.degrees(self.GetAbsoluteRotationAroundXAxis())
    
    def GetRotationAroundXAxisRelativeToSetup(self, otherSetup: Setup) -> float:
        return self.GetRotationAroundXAxisRelativeTo(otherSetup)
    
    def GetRotationAroundXAxisRelativeTo(self, zNormalOrSetup: Union[Vector3D, Setup], yNormal: Optional[Vector3D] = None) -> float:
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
        zNormal: Vector3D
        if isinstance(zNormalOrSetup, Setup) and yNormal is None: # unwrap if a Setup is given
            yNormal = zNormalOrSetup.yNormal
            zNormal = zNormalOrSetup.zNormal
        elif isinstance(zNormalOrSetup, Vector3D):
            zNormal = zNormalOrSetup
            if yNormal is None:
                raise ValueError("yNormal can not be None")
        else:
            raise TypeError("Expected Setup or Vector3D")

        def project(v: Vector3D, n: Vector3D) -> Vector3D:
            d = n.dotProduct(v)
            return Vector3D.create(v.x - n.x * d, v.y - n.y * d, v.z - n.z * d)

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
            newName = re.sub(find, replace, self.ctx.setup.name)
        else:
            if find == "":
                # special case, prepend
                newName = replace + self.ctx.setup.name
            else:
                newName = self.ctx.setup.name.replace(find, replace)

        if self.ctx.setup.name != newName:
            self.ctx.setup.name = newName
    
    def Parse(self, tmpPath: Path):
        from ...programs import Programs

        # JIT parsing of operations to make sure that if settings are 
        # changed while the dialog is open, they are applied to all 
        # setups and operations. 
        # Also, avoids parsing operations for setups that are not 
        # selected or are suppressed, which can speed up processing 
        # and avoid creating temporary files for those setups.
        self.ctx.operations = (None if 
                               not (self.ctx.isSelected
                                    and not (self.ctx.isSuppressed or self.ctx.hasError))
                               else Operations(OperationsContext(), [operation for x in self.ctx.setup.allOperations 
                                                                     if (operation := adskOperation.cast(x)) is not None]))


        if self.ctx.operations is None:
            return # Don't process this setup.

        # Don't spam the user with temporary files that will be deleted anyway
        if Programs.Current is not None:
            Programs.Current.DisableOpenInEditor()

        # Make sure that the setup has all its toolpaths generated
        Programs.CheckAndGenerateToolpath(self.ctx.setup)

        self.ctx.operations.Parse(tmpPath)

    def WriteHeader(self) -> None: writeHeader(self.ctx)
    def WriteHeaderStart(self) -> None: writeHeaderStart(self.ctx)
    def WriteToolComments(self) -> None: writeToolComments(self.ctx)
    def WriteHeaderEnd(self) -> None: writeHeaderEnd(self.ctx)
    def WriteBody(self) -> None: writeBody(self.ctx)
    def WriteTail(self) -> None: writeTail(self.ctx)