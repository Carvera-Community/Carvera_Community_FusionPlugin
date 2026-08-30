from pathlib import Path
from types import SimpleNamespace

import pytest

from addin_import import import_addin_module


header_writer = import_addin_module("commands.postProcessor.operations.header_writer")
Constants = import_addin_module(
    "commands.postProcessor.settings.constants"
).Constants
OperationsHeaderWriterSettings = header_writer.OperationsHeaderWriterSettings


class FakeOperation:
    def __init__(self, tool_id: int | None, file_name: str = "operation"):
        self.toolId = tool_id
        self.fileName = file_name
        self.lineNumber = None

    def SetLineNumber(self, line_number: int) -> None:
        self.lineNumber = line_number

    def WriteHeaderStart(self, output) -> None:
        output.write(f"HEADER T{self.toolId}\n")

    def WriteToolComment(self, output) -> None:
        output.write(f"TOOL T{self.toolId}\n")

    def WriteHeaderEnd(self, output) -> None:
        output.write("HEADER END\n")


def context(tmp_path: Path, operations, file_name="setup"):
    return SimpleNamespace(
        operations=operations,
        path=tmp_path,
        fileName=file_name,
        fileExtension=".nc",
    )


def settings(grouping, overwrite=False):
    return OperationsHeaderWriterSettings(
        overwriteFiles=overwrite,
        operationsGrouping=grouping,
    )


def assign_operation_name(ctx, operation, tool_index):
    operation.fileName = f"{ctx.fileName}_T{operation.toolId}_{tool_index}"


def test_first_header_start_creates_shared_output_file(tmp_path):
    ctx = context(tmp_path, [FakeOperation(7)])

    header_writer.writeFirstHeaderStart(
        ctx, settings(Constants.OperationsGroupings.SETUP)
    )

    assert (tmp_path / "setup.nc").read_text() == "HEADER T7\n"


def test_first_header_start_rejects_existing_file_without_overwrite(tmp_path):
    path = tmp_path / "setup.nc"
    path.write_text("existing", encoding="utf-8")
    ctx = context(tmp_path, [FakeOperation(7)])

    with pytest.raises(FileExistsError, match="overwrite is not allowed"):
        header_writer.writeFirstHeaderStart(
            ctx, settings(Constants.OperationsGroupings.SETUP)
        )

    assert path.read_text(encoding="utf-8") == "existing"


def test_first_header_start_can_overwrite_existing_file(tmp_path):
    path = tmp_path / "setup.nc"
    path.write_text("existing", encoding="utf-8")
    ctx = context(tmp_path, [FakeOperation(7)])

    header_writer.writeFirstHeaderStart(
        ctx,
        settings(Constants.OperationsGroupings.SETUP, overwrite=True),
    )

    assert path.read_text(encoding="utf-8") == "HEADER T7\n"


def test_shared_header_collects_tool_comments_and_first_header_end(tmp_path):
    ctx = context(tmp_path, [FakeOperation(7), FakeOperation(8)])
    header_writer.writeFirstHeaderStart(
        ctx, settings(Constants.OperationsGroupings.SETUP)
    )

    header_writer.writeToolComments(ctx)
    header_writer.writeFirstHeaderEnd(ctx)

    assert (tmp_path / "setup.nc").read_text() == (
        "HEADER T7\nTOOL T7\nTOOL T8\nHEADER END\n"
    )


def test_per_operation_writes_complete_header_to_each_file(tmp_path):
    operations = [FakeOperation(7), FakeOperation(8)]
    ctx = context(tmp_path, operations)

    header_writer.writeHeader(
        ctx,
        settings(Constants.OperationsGroupings.PER_OPERATION),
        assign_operation_name,
    )

    assert (tmp_path / "setup_T7_1.nc").read_text() == (
        "HEADER T7\nTOOL T7\nHEADER END\n"
    )
    assert (tmp_path / "setup_T8_1.nc").read_text() == (
        "HEADER T8\nTOOL T8\nHEADER END\n"
    )
    assert [operation.lineNumber for operation in operations] == [0, 0]


def test_setup_and_tool_starts_header_for_each_tool_change(tmp_path):
    operations = [FakeOperation(7), FakeOperation(8)]
    ctx = context(tmp_path, operations)

    header_writer.writeHeader(
        ctx,
        settings(Constants.OperationsGroupings.SETUP_AND_TOOL),
        assign_operation_name,
    )

    assert (tmp_path / "setup_T7_1.nc").read_text() == (
        "HEADER T7\nTOOL T7\nHEADER END\n"
    )
    assert (tmp_path / "setup_T8_1.nc").read_text() == (
        "HEADER T8\nTOOL T8\nHEADER END\n"
    )
