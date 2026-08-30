from io import StringIO
from pathlib import Path

from addin_import import import_addin_module


OperationContext = import_addin_module(
    "commands.postProcessor.operations.operation.operation_context"
).OperationContext
tail_writer = import_addin_module(
    "commands.postProcessor.operations.operation.tail_writer"
)
TailWriterSettings = tail_writer.TailWriterSettings


class FakeFileNameTarget:
    def __init__(self, file_name: str | None):
        self.fileName = file_name

    def SetFileName(self, file_name: str) -> None:
        self.fileName = file_name


def tail_settings(**overrides) -> TailWriterSettings:
    values = {
        "numericName": False,
        "fileSequenceDigits": 3,
    }
    values.update(overrides)
    return TailWriterSettings(**values)


def write_operation_tail(
    tmp_path: Path,
    contents: str,
    *,
    tail_start: int,
    allow_blank_lines: bool = False,
    settings: TailWriterSettings | None = None,
    file_name_target=None,
) -> str:
    source = tmp_path / "operation.nc"
    source.write_text(contents, encoding="utf-8")
    context = OperationContext(0)
    context.name = "Finishing"
    context.tempFilePath = source
    context.tailStartLine = tail_start
    context.allowBlankLines = allow_blank_lines
    output = StringIO()
    tail_writer.writeTail(
        context,
        output,
        settings or tail_settings(),
        file_name_target,
    )
    return output.getvalue()


def test_write_tail_streams_from_detected_tail_line(tmp_path):
    output = write_operation_tail(
        tmp_path,
        "G1 X10\nM5\nM9\nM30\n",
        tail_start=1,
    )

    assert output == "(Finishing)\nM5\nM9\nM30\n"


def test_write_tail_preserves_blank_line_convention(tmp_path):
    output = write_operation_tail(
        tmp_path,
        "G1 X10\nM30\n",
        tail_start=1,
        allow_blank_lines=True,
    )

    assert output == "\n(Finishing)\nM30\n"


def test_write_tail_increments_numeric_program_name(tmp_path):
    target = FakeFileNameTarget("009")

    write_operation_tail(
        tmp_path,
        "M30\n",
        tail_start=0,
        settings=tail_settings(numericName=True),
        file_name_target=target,
    )

    assert target.fileName == "010"


def test_write_tail_does_not_increment_non_numeric_program_name(tmp_path):
    target = FakeFileNameTarget("job")

    write_operation_tail(
        tmp_path,
        "M30\n",
        tail_start=0,
        settings=tail_settings(numericName=True),
        file_name_target=target,
    )

    assert target.fileName == "job"


def test_write_tail_can_run_without_a_program(tmp_path):
    output = write_operation_tail(
        tmp_path,
        "M30\n",
        tail_start=0,
        settings=tail_settings(numericName=True),
        file_name_target=None,
    )

    assert output == "(Finishing)\nM30\n"
