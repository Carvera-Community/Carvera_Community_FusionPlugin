from pathlib import Path

from ..settings.settings import Settings
from ..file_modes import FileModes

from .operation.operation import Operation
from .operations_context import OperationsContext

def writeBody(ctx: OperationsContext):
    from .operations import setOperationFileName

    toolIdIndex = {}
    firstOperation: bool = True
    operation: Operation
    for operation in [op for op in ctx.operations if op.hasBody]:
        if firstOperation:
            operation.ctx.rotationAngle = ctx.rotationAngle
            operation.ctx.preserveRotation = ctx.preserveRotation
        else:
            operation.ctx.preserveRotation = False

        toolId = operation.toolId
        if toolId not in toolIdIndex:
            toolIdIndex[toolId] = 0
        toolIdIndex[toolId] += 1

        setOperationFileName(ctx, operation, toolIdIndex[toolId])

        pathToOpen: Path = ctx.path / f"{operation.fileName}{ctx.fileExtension}"
        with pathToOpen.open(FileModes.APPEND) as fileHandle:
            if Settings(Settings.OPERATIONS_GROUPING) in [Settings.OperationsGroupings.SINGLE_FILE, 
                                                            Settings.OperationsGroupings.SETUP]:
                operation.WriteBody(fileHandle)

        if firstOperation:
            firstOperation = False