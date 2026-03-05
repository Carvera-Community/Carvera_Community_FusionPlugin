from pathlib import Path

from ..settings.settings import Settings
from ..file_modes import FileModes

from .operation.operation import Operation
from .operations_context import OperationsContext

def writeBody(ctx: OperationsContext):
    from .operations import setOperationFileName

    toolIdIndex = {}
    operation: Operation
    for operation in [op for op in ctx.operations if op.hasBody]:
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

            ctx.rotationAngle = None # Only apply rotation to the first operation if specified as the rotation is applied on a setup level
            ctx.preserveRotation = False # Only preserve rotation for the first operation if specified as the rotation is applied on a setup level
