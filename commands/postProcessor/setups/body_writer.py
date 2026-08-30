from dataclasses import dataclass
from typing import Iterable, Protocol

from ..settings.settings import Settings
from ..settings.constants import Constants


class ResultOperationContext(Protocol):
    isLastOp: bool


class ResultOperation(Protocol):
    hasBody: bool
    ctx: ResultOperationContext


class SetupOperations(Protocol):
    fileName: str | None

    def __iter__(self) -> Iterable[ResultOperation]: ...


class RoutedSetupContext(Protocol):
    operations: SetupOperations | None
    rotationAngle: float | None
    preserveRotation: bool

    def SetFileName(self, fileName: str) -> None: ...


class RoutedSetup(Protocol):
    ctx: RoutedSetupContext

    def WriteBody(self) -> None: ...
    def GetRotationAroundXAxisRelativeToDeg(self, otherSetup) -> float: ...


class SetupsBodyContext(Protocol):
    selected: list[RoutedSetup]
    fileName: str | None
    processingSettings: object | None


@dataclass(frozen=True)
class SetupsBodyWriterSettings:
    operationsGrouping: Constants.OperationsGroupings
    numericName: bool
    rotateAAxis: bool

    @classmethod
    def fromProcessingSettings(cls, settings):
        return cls(settings.operationsGrouping, settings.numericName, settings.rotateAAxis)

    @classmethod
    def fromCurrentSettings(cls) -> "SetupsBodyWriterSettings":
        return cls(
            operationsGrouping=Settings.Get(Settings.OPERATIONS_GROUPING),
            numericName=bool(Settings.Get(Settings.NUMERIC_NAME)),
            rotateAAxis=bool(Settings.Get(Settings.ROTATE_A_AXIS)),
        )


def writeBody(
    ctx: SetupsBodyContext,
    settings: SetupsBodyWriterSettings | None = None,
):
    settings = settings or (SetupsBodyWriterSettings.fromProcessingSettings(ctx.processingSettings) if getattr(ctx, "processingSettings", None) else SetupsBodyWriterSettings.fromCurrentSettings())
    firstSetup: RoutedSetup | None = None
    currentRotationAngle: float | None = None

    operationsGrouping = settings.operationsGrouping
    numericName = settings.numericName
    rotateAAxis = settings.rotateAAxis

    singleFile = (
        operationsGrouping
        == Constants.OperationsGroupings.SINGLE_FILE
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

        if operationsGrouping == Constants.OperationsGroupings.SINGLE_FILE:
            if allOperations:
                allOperations[-1].ctx.isLastOp = True
        elif operationsGrouping == Constants.OperationsGroupings.SETUP:
            for operations in operationsBySetup:
                operations[-1].ctx.isLastOp = True
        else:
            # SETUP_AND_TOOL and PER_OPERATION produce one result file for
            # each internal operation group. Each group is therefore the
            # final operation in its own result file.
            for operation in allOperations:
                operation.ctx.isLastOp = True

    def _getRotation(
        setup: RoutedSetup,
        firstSetup: RoutedSetup | None,
        currentRotation: float | None,
    ) -> tuple[float | None, float | None, bool]:

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
