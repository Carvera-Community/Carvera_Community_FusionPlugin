from __future__ import annotations

from .setups_context import SetupsContext


def _log(message: str) -> None:
    from ....lib.fusionAddInUtils.general_utils import Utils

    Utils.log(message)

def getWCSAlignmentIssues(ctx: SetupsContext) -> tuple[bool, list[str], list[str]]:
    misalignedOrigin = []
    misalignedXAxis = []
    first = None
    for setup in ctx.selected:
        if first is None:
            first = setup
        else:
            if not first.origin.isEqualTo(setup.origin):
                misalignedOrigin.append(setup.name)
            if not first.xNormal.isParallelTo(setup.xNormal):
                misalignedXAxis.append(setup.name)
    return (len(misalignedOrigin) + len(misalignedXAxis) == 0, misalignedOrigin, misalignedXAxis)

def aAxisRotationRequired(ctx: SetupsContext) -> tuple[bool, list[tuple[str, float]]]:
    needsRotation = []
    first = None
    for setup in ctx.selected:
        if first is None:
            first = setup
        else:
            signed_angle = round(first.GetRotationAroundXAxisRelativeToDeg(setup), 3)
            if signed_angle != 0:
                needsRotation.append((setup.name, signed_angle))
                _log(f"Setups: WCS needs rotation: {signed_angle} degrees difference.")
    return (len(needsRotation) != 0, needsRotation)
