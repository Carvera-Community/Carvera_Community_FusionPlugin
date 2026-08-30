from dataclasses import dataclass
from typing import Protocol

from ..settings.settings import Settings
from ..settings.constants import Constants


class SetupTailOperations(Protocol):
    fileName: str | None


class RoutedSetupTailContext(Protocol):
    hasTail: bool
    operations: SetupTailOperations | None

    def SetFileName(self, fileName: str) -> None: ...


class RoutedTailSetup(Protocol):
    ctx: RoutedSetupTailContext

    def WriteTail(self) -> None: ...


class SetupsTailContext(Protocol):
    selected: list[RoutedTailSetup]
    processingSettings: object | None


@dataclass(frozen=True)
class SetupsTailWriterSettings:
    operationsGrouping: Constants.OperationsGroupings
    numericName: bool

    @classmethod
    def fromProcessingSettings(cls, settings):
        return cls(settings.operationsGrouping, settings.numericName)

    @classmethod
    def fromCurrentSettings(cls) -> "SetupsTailWriterSettings":
        return cls(
            operationsGrouping=Settings.Get(Settings.OPERATIONS_GROUPING),
            numericName=bool(Settings.Get(Settings.NUMERIC_NAME)),
        )


def writeTail(
    ctx: SetupsTailContext,
    settings: SetupsTailWriterSettings | None = None,
):
    settings = settings or (SetupsTailWriterSettings.fromProcessingSettings(ctx.processingSettings) if getattr(ctx, "processingSettings", None) else SetupsTailWriterSettings.fromCurrentSettings())

    if settings.operationsGrouping == Constants.OperationsGroupings.SINGLE_FILE:
        firstSetup = next((setup for setup in ctx.selected if setup.ctx.hasTail), None)

        if firstSetup is not None:
            firstSetup.WriteTail()
    else: # SETUP, SETUP_AND_TOOL, PER_OPERATION
        fileName = None
        for setup in ctx.selected:
            if settings.numericName and fileName is not None:
                setup.ctx.SetFileName(fileName)
            setup.WriteTail()
            if settings.numericName and setup.ctx.operations is not None:
                fileName = setup.ctx.operations.fileName
