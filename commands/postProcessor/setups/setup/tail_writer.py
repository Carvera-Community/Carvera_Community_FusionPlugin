from dataclasses import dataclass
from typing import Protocol

from ...settings.settings import Settings
from ...settings.constants import Constants


class SetupTailOperations(Protocol):
    hasTail: bool

    def WriteFirstTail(self) -> None: ...
    def WriteTail(self) -> None: ...


class SetupTailContext(Protocol):
    operations: SetupTailOperations | None
    processingSettings: object | None


@dataclass(frozen=True)
class SetupTailWriterSettings:
    operationsGrouping: Constants.OperationsGroupings

    @classmethod
    def fromProcessingSettings(cls, settings):
        return cls(settings.operationsGrouping)

    @classmethod
    def fromCurrentSettings(cls) -> "SetupTailWriterSettings":
        return cls(
            operationsGrouping=Settings.Get(Settings.OPERATIONS_GROUPING),
        )


def writeTail(
    ctx: SetupTailContext,
    settings: SetupTailWriterSettings | None = None,
):
    settings = settings or (SetupTailWriterSettings.fromProcessingSettings(ctx.processingSettings) if getattr(ctx, "processingSettings", None) else SetupTailWriterSettings.fromCurrentSettings())
    if ctx.operations is None or not ctx.operations.hasTail:
        return

    # SINGLE_FILE and SETUP use one shared result file at this level.
    if settings.operationsGrouping in (
        Constants.OperationsGroupings.SINGLE_FILE,
        Constants.OperationsGroupings.SETUP,
    ):
        ctx.operations.WriteFirstTail()
    else:  # SETUP_AND_TOOL, PER_OPERATION
        ctx.operations.WriteTail()
