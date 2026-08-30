from dataclasses import dataclass
from typing import Protocol

from ...settings.settings import Settings
from ...settings.constants import Constants


class SetupHeaderOperations(Protocol):
    fileName: str | None

    def SetFileName(self, fileName: str) -> None: ...
    def WriteFirstHeaderStart(self) -> None: ...
    def WriteToolComments(self) -> None: ...
    def WriteFirstHeaderEnd(self) -> None: ...
    def WriteHeader(self) -> None: ...


class SetupHeaderContext(Protocol):
    operations: SetupHeaderOperations | None
    index: int
    name: str


@dataclass(frozen=True)
class SetupHeaderWriterSettings:
    numericName: bool
    operationsGrouping: Constants.OperationsGroupings
    fileSequence: bool
    fileSequenceDigits: int

    @classmethod
    def fromCurrentSettings(cls) -> "SetupHeaderWriterSettings":
        return cls(
            numericName=bool(Settings.Get(Settings.NUMERIC_NAME)),
            operationsGrouping=Settings.Get(Settings.OPERATIONS_GROUPING),
            fileSequence=bool(Settings.Get(Settings.FILE_SEQUENCE)),
            fileSequenceDigits=Settings.Get(Settings.FILE_SEQUENCE_DIGITS),
        )


def writeHeaderStart(ctx: SetupHeaderContext) -> None:
    if ctx.operations is None:
        raise ValueError("ctx.operations is None")

    ctx.operations.WriteFirstHeaderStart()

def writeToolComments(ctx: SetupHeaderContext) -> None:
    if ctx.operations is None:
        raise ValueError("_operations is None")

    ctx.operations.WriteToolComments()

def writeHeaderEnd(
    ctx: SetupHeaderContext,
    settings: SetupHeaderWriterSettings | None = None,
) -> None:
    settings = settings or SetupHeaderWriterSettings.fromCurrentSettings()
    if ctx.operations is None:
        raise ValueError("_operations is None")

    ctx.operations.WriteFirstHeaderEnd()

    # Bump up the file name for the next setup if numeric naming 
    # is enabled and we're not in SINGLE_FILE mode 
    # (which doesn't increment file names)
    if (
        settings.numericName
        and settings.operationsGrouping == Constants.OperationsGroupings.SETUP
    ):
            if ctx.operations.fileName is None:
                raise ValueError("_operations.fileName is None")
            ctx.operations.SetFileName(
                str(int(ctx.operations.fileName) + 1).rjust(
                    settings.fileSequenceDigits, "0"
                )
            )

def writeHeader(
    ctx: SetupHeaderContext,
    settings: SetupHeaderWriterSettings | None = None,
) -> None:
    settings = settings or SetupHeaderWriterSettings.fromCurrentSettings()

    if ctx.operations is None:
        raise ValueError("ctx.operations is None")

    if settings.fileSequence:
        fileNumber = str(ctx.index + 1).rjust(settings.fileSequenceDigits, "0")
        ctx.operations.SetFileName(f"{fileNumber}_{ctx.name}")
    else:
        ctx.operations.SetFileName(ctx.name)

    # SETUP writes one setup per file
    if settings.operationsGrouping == Constants.OperationsGroupings.SETUP:
        writeHeaderStart(ctx)
        writeToolComments(ctx)
        writeHeaderEnd(ctx, settings)
    else: # SETUP_AND_TOOL and PER_OPERATION breaks the setup down further
        if ctx.operations is None:
            raise ValueError("ctx.operations is None")
        ctx.operations.WriteHeader()
