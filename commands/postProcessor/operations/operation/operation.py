from pathlib import Path
from typing import Any, Optional, Protocol, TextIO

from ...parameters import Parameters
from ...strings import Strings
from .parser import parse_file
from .operation_context import OperationContext
from .header_writer import (
    write_header_start,
    write_header_end,
    write_tool_comment,
)
from .body_writer import write_body
from .tail_writer import write_tail
from .temporary_post_processing import create_temporary_operation_file
from ..operation_source import raw_operation


class OperationFusionAdapter(Protocol):
    def get_tool_number(self, operation) -> int: ...
    def max_filename_length(self) -> int: ...


class PostProcessingProgram(Protocol):
    fileExtension: str | None
    Parameters: Parameters

    def set_output_folder(self, folder: Path) -> None: ...
    def post_process(self, operations) -> bool: ...


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
        

    def append(self, operation: Any, index, hasTool: bool):
        self._operationsDict[index] = operation
        if hasTool:
            self.ctx.subOperationIndexWithTool = index

        names = "-".join(operation.name for operation in self._operationsDict.values())
        if len(names) > self._fusionAdapter.max_filename_length() - 10:
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
    def tool_id(self) -> Optional[int]:
        return self._fusionAdapter.get_tool_number(
            self._operationsDict[self.ctx.subOperationIndexWithTool]
        ) if self.has_tool else None

    @property
    def has_tool(self) -> bool:
        return self.ctx.subOperationIndexWithTool != -1 and self._operationsDict[self.ctx.subOperationIndexWithTool].hasToolpath

    @property
    def tool(self) -> Optional[Any]:
        if self.ctx.subOperationIndexWithTool == -1:
            return None
        return self._operationsDict[self.ctx.subOperationIndexWithTool].tool

    @property
    def first_index(self) -> int:
        return min(self._operationsDict.keys())

    @property
    def temp_file_path(self) -> Path:
        return self.ctx.tempFilePath
    
    @property
    def has_header(self) -> bool:
        return self.ctx.analysis.header is not None if self.ctx.analysis else self.ctx.headerEndLine != -1

    @property
    def has_body(self) -> bool:
        return self.ctx.analysis.body is not None if self.ctx.analysis else self.ctx.bodyStartLine != -1
    
    @property
    def has_tail(self) -> bool:
        return self.ctx.analysis.tail is not None if self.ctx.analysis else self.ctx.tailStartLine != -1
    
    @property
    def has_rotation(self) -> bool:
        return self.ctx.has_rotation

    def parse(self, tmpPath: Path, program: PostProcessingProgram):
        def postProcess(operations, outputFolder, fileName):
            program.set_output_folder(outputFolder)
            program.parameters.set(Parameters.FILE_NAME, fileName)
            program.parameters.set(Parameters.NAME, fileName)
            return program.post_process(operations)

        create_temporary_operation_file(
            self.ctx,
            tmpPath,
            [raw_operation(operation) for operation in self._operationsDict.values()],
            program.file_extension,
            postProcess,
            parse_file,
        )

    def write_header_start(self, fileHandle: TextIO) -> None: write_header_start(self.ctx, fileHandle)
    def write_header_end(self, fileHandle: TextIO) -> None : write_header_end(self.ctx, fileHandle)
    def write_tool_comment(self, fileHandle: TextIO) -> None: write_tool_comment(self.ctx, fileHandle)
    def write_body(self, fileHandle: TextIO) -> None: write_body(self.ctx, fileHandle)
    def write_tail(self, fileHandle: TextIO) -> None:
        write_tail(self.ctx, fileHandle)
