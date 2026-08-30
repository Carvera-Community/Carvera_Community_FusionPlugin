from io import StringIO
from pathlib import Path

from addin_import import import_addin_module


OperationContext = import_addin_module(
    "commands.postProcessor.operations.operation.operation_context"
).OperationContext
tail_writer = import_addin_module(
    "commands.postProcessor.operations.operation.tail_writer"
)
def write_operation_tail(
    tmp_path: Path,
    contents: str,
    *,
    tail_start: int,
    allow_blank_lines: bool = False,
) -> str:
    source = tmp_path / "operation.nc"
    source.write_text(contents, encoding="utf-8")
    context = OperationContext(0)
    context.name = "Finishing"
    context.tempFilePath = source
    context.tailStartLine = tail_start
    context.allowBlankLines = allow_blank_lines
    output = StringIO()
    tail_writer.writeTail(context, output)
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
