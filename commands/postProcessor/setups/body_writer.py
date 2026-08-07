from typing import Optional, Tuple

from .setups_context import SetupsContext

from ..settings.settings import Settings
from .setup.setup import Setup


def writeBody(ctx: SetupsContext):
    firstSetup: Setup | None = None
    currentRotationAngle: float | None = None

    operationsGrouping = Settings(Settings.OPERATIONS_GROUPING)
    numericName = Settings(Settings.NUMERIC_NAME)
    rotateAAxis = Settings(Settings.ROTATE_A_AXIS)

    singleFile = (
        operationsGrouping
        == Settings.OperationsGroupings.SINGLE_FILE
    )

    fileName: str | None = None

    if numericName:
        fileName = ctx.fileName

    def _getRotation(
        setup: Setup,
        firstSetup: Optional[Setup],
        currentRotation: Optional[float],
    ) -> Tuple[Optional[float], Optional[float], bool]:

        newRotation = None
        preserveRotation = True

        if rotateAAxis:
            if firstSetup is None:
                angle = 0
                preserveRotation = True
            else:
                angle = setup.GetRotationAroundXAxisRelativeToDeg(firstSetup)
                preserveRotation = angle == currentRotation

            if not preserveRotation:
                currentRotation = angle
                newRotation = angle

        return currentRotation, newRotation, preserveRotation

    for setup in ctx.selected:
        currentRotationAngle, setup.ctx.rotationAngle, setup.ctx.preserveRotation = _getRotation(
            setup, firstSetup, currentRotationAngle)

        if firstSetup is None:
            firstSetup = setup

        if numericName and fileName is not None:
            setup.ctx.SetFileName(fileName)

        setup.WriteBody()

        if not singleFile and numericName:
            if setup.ctx.operations is None:
                raise ValueError("setup.ctx.operations is None")

            fileName = setup.ctx.operations.fileName