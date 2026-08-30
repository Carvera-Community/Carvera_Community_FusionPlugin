from dataclasses import dataclass
from typing import Iterable, Protocol

from ..settings.settings import Settings
from ..settings.constants import Constants
from ..output_plan import assignFinalOperations, planResultFiles


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

    resultFiles = planResultFiles(ctx.selected, operationsGrouping)
    assignFinalOperations(ctx.selected, resultFiles)

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
