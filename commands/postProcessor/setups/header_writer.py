from dataclasses import dataclass
from typing import Protocol

from ..settings.settings import Settings
from ..settings.constants import Constants


class SetupHeaderOperations(Protocol):
    fileName: str | None


class RoutedSetupHeaderContext(Protocol):
    operations: SetupHeaderOperations | None

    def SetFileName(self, fileName: str) -> None: ...


class RoutedHeaderSetup(Protocol):
    ctx: RoutedSetupHeaderContext
    hasOperationWithHeader: bool

    def WriteHeaderStart(self) -> None: ...
    def WriteToolComments(self) -> None: ...
    def WriteHeaderEnd(self) -> None: ...
    def WriteHeader(self) -> None: ...


class SetupsHeaderContext(Protocol):
    selected: list[RoutedHeaderSetup]
    processingSettings: object | None


@dataclass(frozen=True)
class SetupsHeaderWriterSettings:
    operationsGrouping: Constants.OperationsGroupings
    numericName: bool

    @classmethod
    def fromProcessingSettings(cls, settings):
        return cls(settings.operationsGrouping, settings.numericName)

    @classmethod
    def fromCurrentSettings(cls) -> "SetupsHeaderWriterSettings":
        return cls(
            operationsGrouping=Settings.Get(Settings.OPERATIONS_GROUPING),
            numericName=bool(Settings.Get(Settings.NUMERIC_NAME)),
        )


def writeHeader(
    ctx: SetupsHeaderContext,
    settings: SetupsHeaderWriterSettings | None = None,
):
    settings = settings or (SetupsHeaderWriterSettings.fromProcessingSettings(ctx.processingSettings) if getattr(ctx, "processingSettings", None) else SetupsHeaderWriterSettings.fromCurrentSettings())
    # SINGLE_FILE
    if settings.operationsGrouping == Constants.OperationsGroupings.SINGLE_FILE:
        firstSetup = next((setup for setup in ctx.selected if setup.hasOperationWithHeader), None)
        if firstSetup is not None: 
            firstSetup.WriteHeaderStart()
            for setup in ctx.selected:
                setup.WriteToolComments()
            firstSetup.WriteHeaderEnd()
    else: # SETUP / SETUP_AND_TOOL / PER_OPERATION
        fileName = None
        for setup in ctx.selected:
            if settings.numericName and fileName is not None:
                setup.ctx.SetFileName(fileName)
            # SETUP starts at 0 each loop, the others continue incrementing from previous setup
            setup.WriteHeader()
            if settings.numericName and setup.ctx.operations is not None:
                fileName = setup.ctx.operations.fileName
