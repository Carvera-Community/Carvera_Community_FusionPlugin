from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from ..settings.settings import Settings
from ..settings.constants import Constants
from ..file_modes import FileModes


class HeaderOperation(Protocol):
    toolId: int | None

    def SetLineNumber(self, lineNumber: int) -> None: ...
    def WriteHeaderStart(self, fileHandler) -> None: ...
    def WriteToolComment(self, fileHandler) -> None: ...
    def WriteHeaderEnd(self, fileHandler) -> None: ...


class HeaderContext(Protocol):
    operations: list[HeaderOperation]
    path: Path
    fileName: str
    fileExtension: str


@dataclass(frozen=True)
class OperationsHeaderWriterSettings:
    overwriteFiles: bool
    operationsGrouping: Constants.OperationsGroupings

    @classmethod
    def fromCurrentSettings(cls) -> "OperationsHeaderWriterSettings":
        return cls(
            overwriteFiles=bool(Settings.Get(Settings.OVERWRITE_FILES)),
            operationsGrouping=Settings.Get(Settings.OPERATIONS_GROUPING),
        )


def _currentFileNameSetter():
    from .operations import setOperationFileName

    return setOperationFileName


def writeFirstHeaderStart(
    ctx: HeaderContext,
    settings: OperationsHeaderWriterSettings | None = None,
) -> None:
    settings = settings or OperationsHeaderWriterSettings.fromCurrentSettings()
    # SINGLE_FILE, SETUP
    if len(ctx.operations) != 0:
        pathToOpen: Path = ctx.path / f"{ctx.fileName}{ctx.fileExtension}"

        if pathToOpen.exists() and not settings.overwriteFiles:
            raise FileExistsError(f"File {pathToOpen} already exists and overwrite is not allowed.")
        # Always OVERWRITE on first header as it indcates a new file
        with pathToOpen.open(FileModes.OVERWRITE) as fileHandler:
            ctx.operations[0].WriteHeaderStart(fileHandler)

def writeToolComments(ctx: HeaderContext) -> None:
    # SINGLE_FILE, SETUP
    if len(ctx.operations) == 0:
        return

    toolIdIndex = {}
    for operation in ctx.operations:
        toolId = operation.toolId
        if toolId not in toolIdIndex:
            toolIdIndex[toolId] = 0
        toolIdIndex[toolId] += 1

        pathToOpen: Path = ctx.path / f"{ctx.fileName}{ctx.fileExtension}"
        with pathToOpen.open(FileModes.APPEND) as fileHandler:
            operation.WriteToolComment(fileHandler)

def writeFirstHeaderEnd(ctx: HeaderContext) -> None:
    # SINGLE_FILE, SETUP
    if len(ctx.operations) != 0:
        pathToOpen: Path = ctx.path / f"{ctx.fileName}{ctx.fileExtension}"
        with pathToOpen.open(FileModes.APPEND) as fileHandler:
            ctx.operations[0].WriteHeaderEnd(fileHandler)

def writeHeader(
    ctx: HeaderContext,
    settings: OperationsHeaderWriterSettings | None = None,
    setFileName: Callable | None = None,
) -> None:
    settings = settings or OperationsHeaderWriterSettings.fromCurrentSettings()
    setFileName = setFileName or _currentFileNameSetter()

    # SETUP_AND_TOOL, PER_OPERATION
    if len(ctx.operations) == 0:
        return

    previousTool = None
    toolIdIndex = {}
    for operation in ctx.operations:
        toolId = operation.toolId
        if toolId not in toolIdIndex:
            toolIdIndex[toolId] = 0
        toolIdIndex[toolId] += 1

        setFileName(ctx, operation, toolIdIndex[toolId])

        pathToOpen: Path = ctx.path / f"{operation.fileName}{ctx.fileExtension}"
        if pathToOpen.exists() and not settings.overwriteFiles:
            raise FileExistsError(f"File {pathToOpen} already exists and overwrite is not allowed.")
        with pathToOpen.open(FileModes.OVERWRITE) as fileHandler:
            if settings.operationsGrouping == Constants.OperationsGroupings.PER_OPERATION:
                operation.SetLineNumber(0)
                operation.WriteHeaderStart(fileHandler)
                operation.WriteToolComment(fileHandler)
                operation.WriteHeaderEnd(fileHandler)
            else: # SETUP_AND_TOOL
                toolChange = previousTool is None or previousTool != toolId
                if toolChange: # New tool, new header
                    operation.SetLineNumber(0)
                    operation.WriteHeaderStart(fileHandler)
                
                operation.WriteToolComment(fileHandler)

                if toolChange:
                    operation.WriteHeaderEnd(fileHandler)
        previousTool = toolId            
