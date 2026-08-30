from pathlib import Path
from types import SimpleNamespace

from addin_import import import_addin_module


tail_writer = import_addin_module("commands.postProcessor.operations.tail_writer")
OperationsTailWriterSettings = tail_writer.OperationsTailWriterSettings


class FakeOperation:
    def __init__(self, tool_id: int, tail: str = "TAIL\n"):
        self.toolId = tool_id
        self.tail = tail
        self.fileName = None

    def WriteTail(self, output, fileNameTarget=None) -> None:
        output.write(self.tail)
        self.fileNameTarget = fileNameTarget


def context(tmp_path: Path, operations, operation_with_tail, file_name="setup"):
    return SimpleNamespace(
        operations=operations,
        operationWithTail=operation_with_tail,
        path=tmp_path,
        fileName=file_name,
        fileExtension=".nc",
        fileNameTarget=None,
    )


def settings(numeric=False, digits=3):
    return OperationsTailWriterSettings(
        numericName=numeric,
        fileSequenceDigits=digits,
    )


def assign_tool_name(ctx, operation, tool_index):
    operation.fileName = f"T{operation.toolId}_{tool_index}"


def test_first_tail_appends_detected_tail_to_shared_file(tmp_path):
    operation = FakeOperation(7, "M30\n")
    ctx = context(tmp_path, [operation], operation)
    (tmp_path / "setup.nc").write_text("BODY\n", encoding="utf-8")

    tail_writer.writeFirstTail(ctx, settings())

    assert (tmp_path / "setup.nc").read_text() == "BODY\nM30\n"


def test_first_tail_does_nothing_without_detected_tail(tmp_path):
    ctx = context(tmp_path, [FakeOperation(7)], None)

    tail_writer.writeFirstTail(ctx, settings())

    assert not (tmp_path / "setup.nc").exists()


def test_first_tail_advances_numeric_context_name(tmp_path):
    operation = FakeOperation(7)
    ctx = context(tmp_path, [operation], operation, file_name="009")

    tail_writer.writeFirstTail(ctx, settings(numeric=True))

    assert ctx.fileName == "010"


def test_split_files_reuse_first_detected_tail(tmp_path):
    operations = [FakeOperation(7), FakeOperation(8)]
    first_tail = FakeOperation(7, "M5\nM30\n")
    ctx = context(tmp_path, operations, first_tail)
    (tmp_path / "T7_1.nc").write_text("BODY 7\n", encoding="utf-8")
    (tmp_path / "T8_1.nc").write_text("BODY 8\n", encoding="utf-8")

    tail_writer.writeTail(ctx, assign_tool_name)

    assert (tmp_path / "T7_1.nc").read_text() == "BODY 7\nM5\nM30\n"
    assert (tmp_path / "T8_1.nc").read_text() == "BODY 8\nM5\nM30\n"


def test_split_files_track_repeated_tool_indices(tmp_path):
    operations = [FakeOperation(7), FakeOperation(7)]
    tail = FakeOperation(7, "M30\n")
    ctx = context(tmp_path, operations, tail)

    tail_writer.writeTail(ctx, assign_tool_name)

    assert (tmp_path / "T7_1.nc").read_text() == "M30\n"
    assert (tmp_path / "T7_2.nc").read_text() == "M30\n"
