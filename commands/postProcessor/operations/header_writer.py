from pathlib import Path
from typing import Optional, TextIO

from .operations_context import OperationsContext

from ..settings.settings import Settings
from ..file_modes import FileModes
from .operation.operation import Operation

def writeFirstHeaderStart(ctx: OperationsContext) -> None:
    # SINGLE_FILE, SETUP
    if len(ctx.operations) != 0:
        pathToOpen: Path = ctx.path / f"{ctx.fileName}{ctx.fileExtension}"

        if pathToOpen.exists() and not Settings(Settings.OVERWRITE_FILES):
            raise FileExistsError(f"File {pathToOpen} already exists and overwrite is not allowed.")
        # Always OVERWRITE on first header as it indcates a new file
        with pathToOpen.open(FileModes.OVERWRITE) as fileHandler:
            ctx.operations[0].WriteHeaderStart(fileHandler)

def writeToolComments(ctx: OperationsContext) -> None:
    # SINGLE_FILE, SETUP
    if len(ctx.operations) == 0:
        return

    toolIdIndex = {}
    fileHandler: Optional[TextIO] = None

    for operation in ctx.operations:
        toolId = operation.toolId
        if toolId not in toolIdIndex:
            toolIdIndex[toolId] = 0
        toolIdIndex[toolId] += 1

        pathToOpen: Path = ctx.path / f"{ctx.fileName}{ctx.fileExtension}"
        with pathToOpen.open(FileModes.APPEND) as fileHandler:
            operation.WriteToolComment(fileHandler)

def writeFirstHeaderEnd(ctx: OperationsContext) -> None:
    # SINGLE_FILE, SETUP
    if len(ctx.operations) != 0:
        pathToOpen: Path = ctx.path / f"{ctx.fileName}{ctx.fileExtension}"
        with pathToOpen.open(FileModes.APPEND) as fileHandler:
            ctx.operations[0].WriteHeaderEnd(fileHandler)

def writeHeader(ctx: OperationsContext) -> None:
    from .operations import setOperationFileName

    # SETUP_AND_TOOL, PER_OPERATION
    if len(ctx.operations) == 0:
        return

    previousTool = None
    toolIdIndex = {}
    operation: Operation
    for operation in ctx.operations:
        toolId = operation.toolId
        if toolId not in toolIdIndex:
            toolIdIndex[toolId] = 0
        toolIdIndex[toolId] += 1

        setOperationFileName(ctx, operation, toolIdIndex[toolId])

        pathToOpen: Path = ctx.path / f"{operation.fileName}{ctx.fileExtension}"
        if pathToOpen.exists() and not Settings(Settings.OVERWRITE_FILES):
            raise FileExistsError(f"File {pathToOpen} already exists and overwrite is not allowed.")
        with pathToOpen.open(FileModes.OVERWRITE) as fileHandler:
            if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.PER_OPERATION:
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
