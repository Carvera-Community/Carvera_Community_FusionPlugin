from pathlib import Path
from typing import Any, Optional, Protocol, TextIO

from ...parameters import Parameters
from ...strings import Strings
from .parser import parseFile
from .operation_context import OperationContext
from .header_writer import (
    writeHeaderStart,
    writeHeaderEnd,
    writeToolComment,
    writeHeader
)
from .body_writer import writeBody
from .tail_writer import writeTail
from .temporary_post_processing import createTemporaryOperationFile
from ..operation_source import raw_operation


class OperationFusionAdapter(Protocol):
    def getToolNumber(self, operation) -> int: ...
    def maxFilenameLength(self) -> int: ...


class PostProcessingProgram(Protocol):
    fileExtension: str | None
    Parameters: Parameters

    def SetOutputFolder(self, folder: Path) -> None: ...
    def PostProcess(self, operations) -> bool: ...


class Operation():    
    def __init__(
        self,
        ctx: OperationContext,
        fusionAdapter: OperationFusionAdapter | None = None,
    ):
        if fusionAdapter is None:
            from ...fusion_adapters.operations import FusionOperationAdapter

            fusionAdapter = FusionOperationAdapter()
        self._fusionAdapter = fusionAdapter
        self.ctx = ctx
        # As there can be multiple operations without tools they are 
        # grouped with the previous operation (or next if it is the 
        # first operation missing a tool)
        self._operationsDict: dict[int, Any] = {}
        

    def Append(self, operation: Any, index, hasTool: bool):
        self._operationsDict[index] = operation
        if hasTool:
            self.ctx.subOperationIndexWithTool = index

        names = "-".join(operation.name for operation in self._operationsDict.values())
        if len(names) > self._fusionAdapter.maxFilenameLength() - 10:
            self.ctx.name = Strings("Combined Operations ({operationsCount})".format(operationsCount=len(self._operationsDict)))
        else:
            self.ctx.name = names


    @property
    def name(self) -> str:
        return self.ctx.name
    
    @property
    def index(self) -> int:
        return self.ctx.index

    @property
    def toolId(self) -> Optional[int]:
        return self._fusionAdapter.getToolNumber(
            self._operationsDict[self.ctx.subOperationIndexWithTool]
        ) if self.hasTool else None

    @property
    def hasTool(self) -> bool:
        return self.ctx.subOperationIndexWithTool != -1 and self._operationsDict[self.ctx.subOperationIndexWithTool].hasToolpath

    @property
    def tool(self) -> Optional[Any]:
        if self.ctx.subOperationIndexWithTool == -1:
            return None
        return self._operationsDict[self.ctx.subOperationIndexWithTool].tool

    @property
    def firstIndex(self) -> int:
        return min(self._operationsDict.keys())

    @property
    def tempFilePath(self) -> Path:
        return self.ctx.tempFilePath
    
    @property
    def hasHeader(self) -> bool:
        return self.ctx.analysis.header is not None if self.ctx.analysis else self.ctx.headerEndLine != -1

    @property
    def hasBody(self) -> bool:
        return self.ctx.analysis.body is not None if self.ctx.analysis else self.ctx.bodyStartLine != -1
    
    @property
    def hasTail(self) -> bool:
        return self.ctx.analysis.tail is not None if self.ctx.analysis else self.ctx.tailStartLine != -1
    
    @property
    def hasRotation(self) -> bool:
        return self.ctx.hasRotation

    def Parse(self, tmpPath: Path, program: PostProcessingProgram):
        def postProcess(operations, outputFolder, fileName):
            program.SetOutputFolder(outputFolder)
            program.Parameters.Set(Parameters.FILE_NAME, fileName)
            program.Parameters.Set(Parameters.NAME, fileName)
            return program.PostProcess(operations)

        createTemporaryOperationFile(
            self.ctx,
            tmpPath,
            [raw_operation(operation) for operation in self._operationsDict.values()],
            program.fileExtension,
            postProcess,
            parseFile,
        )

    def WriteHeaderStart(self, fileHandle: TextIO) -> None: writeHeaderStart(self.ctx, fileHandle)
    def WriteHeaderEnd(self, fileHandle: TextIO) -> None : writeHeaderEnd(self.ctx, fileHandle)
    def WriteToolComment(self, fileHandle: TextIO) -> None: writeToolComment(self.ctx, fileHandle)
    def WriteHeader(self, fileHandle: TextIO) -> None: writeHeader(self.ctx, fileHandle)
    def WriteBody(self, fileHandle: TextIO) -> None: writeBody(self.ctx, fileHandle)
    def WriteTail(self, fileHandle: TextIO) -> None:
        writeTail(self.ctx, fileHandle)
