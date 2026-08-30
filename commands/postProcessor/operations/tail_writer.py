from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from ..file_modes import FileModes
from ..settings.settings import Settings


class TailOperation(Protocol):
    toolId: int | None
    fileName: str

    def WriteTail(self, fileHandler, fileNameTarget=None) -> None: ...


class TailContext(Protocol):
    operations: list[TailOperation]
    operationWithTail: TailOperation | None
    fileNameTarget: object | None
    path: Path
    fileName: str
    fileExtension: str


@dataclass(frozen=True)
class OperationsTailWriterSettings:
    numericName: bool
    fileSequenceDigits: int

    @classmethod
    def fromCurrentSettings(cls) -> "OperationsTailWriterSettings":
        return cls(
            numericName=bool(Settings.Get(Settings.NUMERIC_NAME)),
            fileSequenceDigits=Settings.Get(Settings.FILE_SEQUENCE_DIGITS),
        )


def _currentFileNameSetter():
    from .operations import setOperationFileName

    return setOperationFileName


def writeFirstTail(
    ctx: TailContext,
    settings: OperationsTailWriterSettings | None = None,
) -> None:
    settings = settings or OperationsTailWriterSettings.fromCurrentSettings()
    # SINGLE_FILE, SETUP

    if ctx.operationWithTail is None:
        return

    pathToOpen: Path = ctx.path / f"{ctx.fileName}{ctx.fileExtension}"
    with pathToOpen.open(FileModes.APPEND) as fileHandler:
        ctx.operationWithTail.WriteTail(fileHandler, ctx.fileNameTarget)
    if settings.numericName:
        ctx.fileName = str(int(ctx.fileName) + 1).rjust(
            settings.fileSequenceDigits, "0"
        )

def writeTail(ctx: TailContext, setFileName: Callable | None = None):
    # SETUP_AND_TOOL, PER_OPERATION
    setFileName = setFileName or _currentFileNameSetter()

    if ctx.operationWithTail is None:
        return 

    toolIdIndex = {}
    for operation in ctx.operations:
        toolId = operation.toolId
        if toolId not in toolIdIndex:
            toolIdIndex[toolId] = 0
        toolIdIndex[toolId] += 1

        setFileName(ctx, operation, toolIdIndex[toolId])

        pathToOpen: Path = ctx.path / f"{operation.fileName}{ctx.fileExtension}"
        with pathToOpen.open(FileModes.APPEND) as fileHandler:
            ctx.operationWithTail.WriteTail(fileHandler, ctx.fileNameTarget)
