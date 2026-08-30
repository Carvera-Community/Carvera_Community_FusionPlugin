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

    def _markLastOperationsInResultFiles() -> None:
        operationsBySetup = []
        allOperations = []

        for setup in ctx.selected:
            operations = setup.ctx.operations
            if operations is None:
                continue

            for operation in operations:
                operation.ctx.isLastOp = False

            bodyOperations = [operation for operation in operations if operation.hasBody]
            if bodyOperations:
                operationsBySetup.append(bodyOperations)
                allOperations.extend(bodyOperations)

        if operationsGrouping == Settings.OperationsGroupings.SINGLE_FILE:
            if allOperations:
                allOperations[-1].ctx.isLastOp = True
        elif operationsGrouping == Settings.OperationsGroupings.SETUP:
            for operations in operationsBySetup:
                operations[-1].ctx.isLastOp = True
        else:
            # SETUP_AND_TOOL and PER_OPERATION produce one result file for
            # each internal operation group. Each group is therefore the
            # final operation in its own result file.
            for operation in allOperations:
                operation.ctx.isLastOp = True

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

    _markLastOperationsInResultFiles()

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
