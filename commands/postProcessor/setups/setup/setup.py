from __future__ import annotations

import math
from pathlib import Path
import re

from typing import (
    Any,
    Callable,
    Optional, 
    Protocol,
    Union,
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
from .vector_rotation import getSignedRotationAroundAxis


class SetupFusionAdapter(Protocol):
    def origin(self, setup): ...
    def normal(self, setup, direction: tuple[float, float, float]): ...
    def globalVector(self, direction: tuple[float, float, float]): ...
    def castOperation(self, value): ...

class Setup():
    def __init__(
        self,
        ctx: SetupContext,
        setup: Any,
        index: int,
        isDefaultSelected: bool = False,
        fusionAdapter: SetupFusionAdapter | None = None,
        operationsFactory: Callable = Operations,
        programRegistry=None,
    ):
        if fusionAdapter is None:
            from ...fusion_adapters.setup import FusionSetupAdapter

            fusionAdapter = FusionSetupAdapter()
        self._fusionAdapter = fusionAdapter
        self._operationsFactory = operationsFactory
        self._programRegistry = programRegistry
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
    def origin(self):
        return self._fusionAdapter.origin(self.ctx.setup)

    @property
    def zNormal(self):
        return self._fusionAdapter.normal(self.ctx.setup, (0, 0, 1))
    
    @property
    def xNormal(self):
        return self._fusionAdapter.normal(self.ctx.setup, (1, 0, 0))

    @property
    def yNormal(self):
        return self._fusionAdapter.normal(self.ctx.setup, (0, 1, 0))

    @property
    def hasMachine(self) -> bool:
        return self.ctx.setup.machine is not None

    @property
    def tools(self) -> list[Any]:
        return self.ctx.operations.tools if self.ctx.operations is not None else []

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
        gZNormal = self._fusionAdapter.globalVector((0, 0, 1))
        gYNormal = self._fusionAdapter.globalVector((0, 1, 0))
        return self.GetRotationAroundXAxisRelativeTo(gZNormal, gYNormal)
    
    def GetAbsoluteRotationAroundXAxisDeg(self) -> float:
        return math.degrees(self.GetAbsoluteRotationAroundXAxis())
    
    def GetRotationAroundXAxisRelativeToSetup(self, otherSetup: Setup) -> float:
        return self.GetRotationAroundXAxisRelativeTo(otherSetup)
    
    def GetRotationAroundXAxisRelativeTo(self, zNormalOrSetup, yNormal=None) -> float:
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
        zNormal = None
        if isinstance(zNormalOrSetup, Setup) and yNormal is None: # unwrap if a Setup is given
            yNormal = zNormalOrSetup.yNormal
            zNormal = zNormalOrSetup.zNormal
        elif all(hasattr(zNormalOrSetup, coordinate) for coordinate in ("x", "y", "z")):
            zNormal = zNormalOrSetup
            if yNormal is None:
                raise ValueError("yNormal can not be None")
        else:
            raise TypeError("Expected Setup or Vector3D")

        def coordinates(vector) -> tuple[float, float, float]:
            return (vector.x, vector.y, vector.z)

        return getSignedRotationAroundAxis(
            sourceDirection=coordinates(self.zNormal),
            targetDirection=coordinates(zNormal),
            rotationAxis=coordinates(xNormal),
            sourceFallback=coordinates(self.yNormal),
            targetFallback=coordinates(yNormal),
        )
    
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
        if self._programRegistry is None:
            from ...programs import Programs

            self._programRegistry = Programs
        programs = self._programRegistry

        # JIT parsing of operations to make sure that if settings are 
        # changed while the dialog is open, they are applied to all 
        # setups and operations. 
        # Also, avoids parsing operations for setups that are not 
        # selected or are suppressed, which can speed up processing 
        # and avoid creating temporary files for those setups.
        self.ctx.operations = (None if 
                               not (self.ctx.isSelected
                                    and not (self.ctx.isSuppressed or self.ctx.hasError))
                               else self._operationsFactory(
                                   OperationsContext(processingSettings=self.ctx.processingSettings),
                                   [operation for x in self.ctx.setup.allOperations
                                    if (operation := self._fusionAdapter.castOperation(x)) is not None],
                               ))


        if not self.ctx.operations:
            return # Don't process this setup.

        # Don't spam the user with temporary files that will be deleted anyway
        program = programs.Current
        if program is None:
            raise ValueError("Programs.Current is None")
        program.DisableOpenInEditor()

        # Make sure that the setup has all its toolpaths generated
        programs.CheckAndGenerateToolpath(self.ctx.setup)

        self.ctx.operations.Parse(tmpPath, program)

    def WriteHeader(self) -> None: writeHeader(self.ctx)
    def WriteHeaderStart(self) -> None: writeHeaderStart(self.ctx)
    def WriteToolComments(self) -> None: writeToolComments(self.ctx)
    def WriteHeaderEnd(self) -> None: writeHeaderEnd(self.ctx)
    def WriteBody(self) -> None: writeBody(self.ctx)
    def WriteTail(self) -> None: writeTail(self.ctx)
