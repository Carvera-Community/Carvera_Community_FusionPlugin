from pathlib import Path
from ..file_modes import FileModes
from ..settings.settings import Settings

from .operations_context import OperationsContext
from .operation.operation import Operation

def writeFirstTail(ctx: OperationsContext) -> None:
    # SINGLE_FILE, SETUP

    if ctx.operationWithTail is None:
        return

    pathToOpen: Path = ctx.path / f"{ctx.fileName}{ctx.fileExtension}"
    with pathToOpen.open(FileModes.APPEND) as fileHandler:
        ctx.operationWithTail.WriteTail(fileHandler)
    if Settings(Settings.NUMERIC_NAME):
        ctx.fileName = str(int(ctx.fileName) + 1).rjust(Settings(Settings.FILE_SEQUENCE_DIGITS), '0')

def writeTail(ctx: OperationsContext):
    # SETUP_AND_TOOL, PER_OPERATION
    from .operations import setOperationFileName

    if ctx.operationWithTail is None:
        return 

    toolIdIndex = {}
    operation: Operation
    for operation in ctx.operations:
        toolId = operation.toolId
        if toolId not in toolIdIndex:
            toolIdIndex[toolId] = 0
        toolIdIndex[toolId] += 1

        setOperationFileName(ctx, operation, toolIdIndex[toolId])

        pathToOpen: Path = ctx.path / f"{operation.fileName}{ctx.fileExtension}"
        with pathToOpen.open(FileModes.APPEND) as fileHandler:
            ctx.operationWithTail.WriteTail(fileHandler)
