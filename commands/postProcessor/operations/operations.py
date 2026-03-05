from pathlib import Path
from typing import Optional, TextIO

from adsk.cam import Operation as adskOperation
from adsk.cam import Tool as adskTool
from .operations_context import OperationsContext
from .operation.operation_context import OperationContext
from ....lib.fusionAddInUtils import Utils
from ..settings.settings import Settings
from .operation.operation import Operation

from .header_writer import (
    writeFirstHeaderStart,
    writeToolComments,
    writeFirstHeaderEnd,
    writeHeader
)
from .body_writer import writeBody
from .tail_writer import (
    writeFirstTail,
    writeTail
)

class Operations():
    def __iter__(self):
        return iter(self.ctx.operations)

    def __len__(self):
        return len(self.ctx.operations)

    def __getitem__(self, index):
        return self.ctx.operations[index]

    def __init__(self, ctx: OperationsContext, adskOperations: list[adskOperation]):
        self.ctx = ctx

        i = 0
        operation = None
        while i < len(adskOperations):
            if(adskOperations[i].isSuppressed):
                i += 1
                continue
            # Look ahead for operations without a toolpath. This can happen
            # with a manual operation. Group it with current operation.
            # Or if first, group it with subsequent ones.
            # Also optionally group together operations with the same tool number

            operationContext = OperationContext(i)
            operation = Operation(operationContext)
            operation.Append(adskOperations[i], i, adskOperations[i].hasToolpath) # add first operation
            i += 1
            while i < len(adskOperations):
                if(adskOperations[i].isSuppressed):
                    i += 1
                    continue
                # Append to current group if:
                # - operation has no toolpath, or
                # - current group has no tool yet (we haven't encountered a toolpath), or
                # - we're grouping operations on setup and tool, or
                # - we're combining tools and this op uses the same tool as the current group
                # otherwise finish current group and start a new one
                if ((not adskOperations[i].hasToolpath) 
                    or (not operation.hasTool) 
                    or (Settings.Get(Settings.COMBINE_TOOL) 
                        and Operation.GetToolNumber(adskOperations[i]) == operation.toolId)):
                    operation.Append(adskOperations[i], i, adskOperations[i].hasToolpath)
                    i += 1
                else:
                    # different tool (or not combining) -> finish current group
                    self.ctx.operations.append(operation)
                    break
        if operation is not None: # append final group
            self.ctx.operations.append(operation)

    @property
    def fileName(self) -> str:
        return self.ctx.fileName
    
    def SetFileName(self, fileName: str) -> None:
        self.ctx.fileName = fileName

    def SetOutputPath(self, path: Path) -> None:
        self.ctx.path = path

    def SetFileExtension(self, extension: str) -> None:
        self.ctx.fileExtension = extension

    @property
    def hasHeader(self):
        return self.ctx.operationWithHeader is not None
    
    @property
    def hasTail(self):
        return self.ctx.operationWithTail is not None

    @property
    def tools(self) -> list[adskTool]:
        tools = list[adskTool]()
        for operation in self.ctx.operations:
            if operation.hasTool and operation.tool is not None and operation.tool not in tools:
                tools.append(operation.tool)
        return tools

    def Parse(self, tmpPath: Path) -> None:
        for operation in self.ctx.operations:
            operation.Parse(tmpPath)
        self.ctx.operationWithTail = next((operation for operation in self.ctx.operations if operation.hasTail), None)
        self.ctx.operationWithHeader = next((operation for operation in self.ctx.operations if operation.hasHeader), None)

    def WriteFirstHeaderStart(self) -> None: writeFirstHeaderStart(self.ctx)
    def WriteToolComments(self) -> None: writeToolComments(self.ctx)
    def WriteFirstHeaderEnd(self) -> None: writeFirstHeaderEnd(self.ctx)
    def WriteHeader(self) -> None: writeHeader(self.ctx)

    def WriteBody(self, rotationAngle: float|None, preserveRotation: bool) -> None: 
        self.ctx.rotationAngle = rotationAngle
        self.ctx.preserveRotation = preserveRotation
        writeBody(self.ctx)

    def WriteFirstTail(self) -> None: writeFirstTail(self.ctx)
    def WriteTail(self) -> None: writeTail(self.ctx)


def setOperationFileName(ctx: OperationsContext, operation: Operation, toolIdIndex: int) -> None:
    
    operation.SetFileName(ctx.fileName)

    if Settings(Settings.OPERATIONS_GROUPING) in [Settings.OperationsGroupings.SINGLE_FILE, 
                                                    Settings.OperationsGroupings.SETUP]:
        return
    
    fileNumber = str((operation.index + 1)).rjust(Settings(Settings.FILE_SEQUENCE_DIGITS), '0')

    if Settings(Settings.NUMERIC_NAME) and ctx.fileName is not None:
        # Bump up the file name for the next operation if numeric naming is set
        ctx.fileName = str(int(ctx.fileName) + 1).rjust(Settings(Settings.FILE_SEQUENCE_DIGITS), '0')
    else:
        if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SETUP_AND_TOOL:
            # For setup and tool grouping, use the tool number as 
            # the file name, and append an index if there are 
            # multiple operations with the same tool
            toolIdStr = f"T{operation.toolId}{'_' + str(toolIdIndex) if toolIdIndex > 1 else ''}"
            if Settings(Settings.FILE_SEQUENCE):
                toolIdStr = f"{fileNumber}_{toolIdStr}"
            operation.SetFileName(Utils.sanitizeFilename(f"{ctx.fileName}_{toolIdStr}", preserveExtension = False))
        elif Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.PER_OPERATION:
            # For per operation grouping, use the operation name as
            # the file name
            if Settings(Settings.FILE_SEQUENCE):
                operation.SetFileName(Utils.sanitizeFilename(f"{fileNumber}_{operation.name}", preserveExtension = False))
            else:
                operation.SetFileName(Utils.sanitizeFilename(operation.name, preserveExtension = False))
