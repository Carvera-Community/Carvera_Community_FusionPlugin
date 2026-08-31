from pathlib import Path
from typing import Any

from .operations_context import OperationsContext
from .operation.operation_context import OperationContext
from .operation.operation import Operation
from .operation_grouping import group_operation_sources


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

        if self.ctx.processingSettings is None:
            raise ValueError("Processing settings are required")
        groups = group_operation_sources(
            adskOperations,
            combineTool=self.ctx.processingSettings.combineTool,
            get_tool_number=fusionAdapter.get_tool_number,
        )
        for group in groups:
            operation = Operation(
                OperationContext(
                    group[0].index,
                    processingSettings=self.ctx.processingSettings,
                ),
                fusionAdapter,
            )
            for item in group:
                operation.append(item.source, item.index, item.source.hasToolpath)
            self.ctx.operations.append(operation)

    @property
    def file_name(self) -> str:
        return self.ctx.file_name
    
    def set_file_name(self, fileName: str) -> None:
        self.ctx.file_name = fileName

    def set_output_path(self, path: Path) -> None:
        self.ctx.path = path

    def set_file_extension(self, extension: str) -> None:
        self.ctx.file_extension = extension

    @property
    def tools(self) -> list[Any]:
        tools = []
        for operation in self.ctx.operations:
            if operation.has_tool and operation.tool is not None and operation.tool not in tools:
                tools.append(operation.tool)
        return tools

    def parse(self, tmpPath: Path, program) -> None:
        for operation in self.ctx.operations:
            operation.parse(tmpPath, program)
        self.ctx.operation_with_tail = next((operation for operation in self.ctx.operations if operation.has_tail), None)
