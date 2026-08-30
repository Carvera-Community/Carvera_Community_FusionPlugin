from pathlib import Path

from adsk.cam import Operation as adskOperation
from adsk.cam import Tool as adskTool
from .operations_context import OperationsContext
from .operation.operation_context import OperationContext
from ....lib.fusionAddInUtils import Utils
from ..settings.settings import Settings
from .operation.operation import Operation
from .operation_file_naming import (
    OperationFileNamingSettings,
    setOperationFileName as applyOperationFileName,
)

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
    settings = OperationFileNamingSettings(
        operationsGrouping=Settings(Settings.OPERATIONS_GROUPING),
        fileSequenceDigits=Settings(Settings.FILE_SEQUENCE_DIGITS),
        numericName=Settings(Settings.NUMERIC_NAME),
        fileSequence=Settings(Settings.FILE_SEQUENCE),
    )
    applyOperationFileName(
        ctx,
        operation,
        toolIdIndex,
        settings,
        lambda name: Utils.sanitizeFilename(name, preserveExtension=False),
    )
