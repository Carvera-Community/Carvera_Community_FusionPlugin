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

from .setup_context import SetupContext

from ...operations.operations import Operations

from .vector_rotation import get_signed_rotation_around_axis
from .setup_processing import process_setup


class SetupFusionAdapter(Protocol):
    def origin(self, setup): ...
    def normal(self, setup, direction: tuple[float, float, float]): ...
    def global_vector(self, direction: tuple[float, float, float]): ...
    def cast_operation(self, value): ...

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
        ctx.setup = (
            fusionAdapter.snapshot_setup(setup)
            if hasattr(fusionAdapter, "snapshot_setup")
            else setup
        )
        ctx.index = index
        ctx.isSelected = isDefaultSelected

    @property
    def index(self) -> int:
        return self.ctx.index
    
    @property
    def isSelected(self) -> bool:
        return self.ctx.isSelected

    def select(self, value: bool):
        self.ctx.isSelected = value

    @property
    def name(self) -> str:
        return self.ctx.setup.name
    
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

    def set_output_path(self, path: Path):
        path.mkdir(parents=True, exist_ok=True)
        if self.ctx.operations is not None:
            self.ctx.operations.set_output_path(path)

    def set_file_extension(self, fileExtension: str):
        if self.ctx.operations is not None:
            self.ctx.operations.set_file_extension(fileExtension)

    # Compute signed rotation around the setup's X axis.
    #
    # Behavior:
    # - `absolute_rotation()` returns the signed rotation (radians)
    #   that aligns the setup's local Z with the global Z, measured around the
    #   setup's local X axis. It is a thin wrapper that calls
    #   `rotation_relative_to(zNormal, yNormal)` with global Z/Y.
    # - `rotation_relative_to(zNormal, yNormal)` computes the
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
    def absolute_rotation(self) -> float:
        gZNormal = self._fusionAdapter.global_vector((0, 0, 1))
        gYNormal = self._fusionAdapter.global_vector((0, 1, 0))
        return self.rotation_relative_to(gZNormal, gYNormal)
    
    def absolute_rotation_degrees(self) -> float:
        return math.degrees(self.absolute_rotation())
    
    def rotation_relative_to_setup(self, otherSetup: Setup) -> float:
        return self.rotation_relative_to(otherSetup)
    
    def rotation_relative_to(self, zNormalOrSetup, yNormal=None) -> float:
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

        return get_signed_rotation_around_axis(
            sourceDirection=coordinates(self.zNormal),
            targetDirection=coordinates(zNormal),
            rotationAxis=coordinates(xNormal),
            sourceFallback=coordinates(self.yNormal),
            targetFallback=coordinates(yNormal),
        )
    
    def rotation_relative_to_degrees(self, otherSetup) -> float:
        return math.degrees(self.rotation_relative_to(otherSetup.zNormal, otherSetup.yNormal))
    
    def rename(self, find, replace, isRegex):
        if isRegex:
            newName = re.sub(find, replace, self.ctx.setup.name)
        else:
            if find == "":
                # special case, prepend
                newName = replace + self.ctx.setup.name
            else:
                newName = self.ctx.setup.name.replace(find, replace)

        if self.ctx.setup.name != newName:
            if hasattr(self._fusionAdapter, "rename_setup"):
                self._fusionAdapter.rename_setup(self.ctx.setup, newName)
            else:
                self.ctx.setup.name = newName
    
    def parse(self, tmpPath: Path):
        if self._programRegistry is None:
            from ...programs import Programs

            self._programRegistry = Programs
        process_setup(
            self.ctx,
            tmpPath,
            self._fusionAdapter,
            self._operationsFactory,
            self._programRegistry,
        )
