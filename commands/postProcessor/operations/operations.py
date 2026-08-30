from pathlib import Path
from typing import Any

from .operations_context import OperationsContext
from .operation.operation_context import OperationContext
from ..settings.settings import Settings
from .operation.operation import Operation
from .operation_grouping import groupOperationSources
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

    def __init__(
        self,
        ctx: OperationsContext,
        adskOperations: list[Any],
        fusionAdapter=None,
    ):
        if fusionAdapter is None:
            from ..fusion_adapters.operations import FusionOperationAdapter

            fusionAdapter = FusionOperationAdapter()
        self.ctx = ctx

        groups = groupOperationSources(
            adskOperations,
            combineTool=bool(Settings.Get(Settings.COMBINE_TOOL)),
            getToolNumber=fusionAdapter.getToolNumber,
        )
        for group in groups:
            operation = Operation(OperationContext(group[0].index), fusionAdapter)
            for item in group:
                operation.Append(item.source, item.index, item.source.hasToolpath)
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
    def tools(self) -> list[Any]:
        tools = []
        for operation in self.ctx.operations:
            if operation.hasTool and operation.tool is not None and operation.tool not in tools:
                tools.append(operation.tool)
        return tools

    def Parse(self, tmpPath: Path, program) -> None:
        self.ctx.fileNameTarget = program
        for operation in self.ctx.operations:
            operation.Parse(tmpPath, program)
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
        lambda name: _sanitizeFilename(name),
    )


def _sanitizeFilename(name: str) -> str:
    from ....lib.fusionAddInUtils import Utils

    return Utils.sanitizeFilename(name, preserveExtension=False)
