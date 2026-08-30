from dataclasses import dataclass
from typing import Protocol

from ...settings.settings import Settings
from ...settings.constants import Constants


class SetupOperations(Protocol):
    fileName: str | None

    def WriteBody(self, rotationAngle: float | None, preserveRotation: bool) -> None: ...
    def SetFileName(self, fileName: str) -> None: ...


class SetupBodyContext(Protocol):
    operations: SetupOperations | None
    rotationAngle: float | None
    preserveRotation: bool
    processingSettings: object | None


@dataclass(frozen=True)
class SetupBodyWriterSettings:
    numericName: bool
    operationsGrouping: Constants.OperationsGroupings
    fileSequenceDigits: int

    @classmethod
    def fromProcessingSettings(cls, settings):
        return cls(settings.numericName, settings.operationsGrouping, settings.fileSequenceDigits)

    @classmethod
    def fromCurrentSettings(cls) -> "SetupBodyWriterSettings":
        return cls(
            numericName=bool(Settings.Get(Settings.NUMERIC_NAME)),
            operationsGrouping=Settings.Get(Settings.OPERATIONS_GROUPING),
            fileSequenceDigits=Settings.Get(Settings.FILE_SEQUENCE_DIGITS),
        )


def writeBody(
    ctx: SetupBodyContext,
    settings: SetupBodyWriterSettings | None = None,
):
    settings = settings or (SetupBodyWriterSettings.fromProcessingSettings(ctx.processingSettings) if getattr(ctx, "processingSettings", None) else SetupBodyWriterSettings.fromCurrentSettings())
    if ctx.operations is None:
        raise ValueError("ctx.operations is None")
    ctx.operations.WriteBody(ctx.rotationAngle, ctx.preserveRotation)

    # Bump up the file name for the next setup if numeric naming 
    # is enabled and we're in SETUP mode
    if (
        settings.numericName
        and settings.operationsGrouping == Constants.OperationsGroupings.SETUP
    ):
            if ctx.operations.fileName is None:
                    raise ValueError("ctx.operations.fileName is None")
            ctx.operations.SetFileName(
                str(int(ctx.operations.fileName) + 1).rjust(
                    settings.fileSequenceDigits, "0"
                )
            )
