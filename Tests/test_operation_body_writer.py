from io import StringIO
from pathlib import Path

from addin_import import import_addin_module


OperationContext = import_addin_module(
    "commands.postProcessor.operations.operation.operation_context"
).OperationContext
body_writer = import_addin_module(
    "commands.postProcessor.operations.operation.body_writer"
)
BodyWriterSettings = body_writer.BodyWriterSettings
writeBody = body_writer.writeBody


def writer_settings(**overrides) -> BodyWriterSettings:
    values = {
        "safeYRetraction": True,
        "yRetractionCoordinate": -100,
    }
    values.update(overrides)
    return BodyWriterSettings(**values)


def write_operation_body(
    tmp_path: Path,
    contents: str,
    *,
    body_start: int,
    tail_start: int,
    settings: BodyWriterSettings | None = None,
    **context_values,
) -> str:
    source = tmp_path / "operation.nc"
    source.write_text(contents, encoding="utf-8")
    context = OperationContext(0)
    context.tempFilePath = source
    context.bodyStartLine = body_start
    context.tailStartLine = tail_start
    for name, value in context_values.items():
        setattr(context, name, value)

    output = StringIO()
    writeBody(context, output, settings or writer_settings())
    return output.getvalue()


def test_write_body_streams_only_body_rows(tmp_path):
    output = write_operation_body(
        tmp_path,
        "(Header)\nT1 M6\nG1 X10\nG1 X20\nM30\n",
        body_start=1,
        tail_start=4,
    )

    assert output == "T1 M6\nG1 X10\nG1 X20\n"


def test_write_body_removes_shrink_from_nonfinal_operation(tmp_path):
    output = write_operation_body(
        tmp_path,
        "T1 M6\nG92.4 A0 R0\nG1 X10\nM30\n",
        body_start=0,
        tail_start=3,
        shrinkLine=1,
        isLastOp=False,
    )

    assert output == "T1 M6\nG1 X10\n"


def test_write_body_preserves_shrink_in_final_operation(tmp_path):
    output = write_operation_body(
        tmp_path,
        "T1 M6\nG92.4 A0 R0\nG1 X10\nM30\n",
        body_start=0,
        tail_start=3,
        shrinkLine=1,
        isLastOp=True,
    )

    assert output == "T1 M6\nG92.4 A0 R0\nG1 X10\n"


def test_write_body_replaces_rotation_with_safe_retraction(tmp_path):
    output = write_operation_body(
        tmp_path,
        "T1 M6\nG0 A0\nG1 X10\nM30\n",
        body_start=0,
        tail_start=3,
        rotationLine=1,
        rotationAngle=45.0,
        preserveRotation=False,
        settings=writer_settings(yRetractionCoordinate=-75),
    )

    assert output == (
        "T1 M6\n"
        "(Rotating a-axis between setups)\n"
        "G90 G53 G0 Z-3 Y-75\n"
        "G90 G54 G0 A45\n"
        "G1 X10\n"
    )


def test_write_body_can_rotate_without_y_retraction(tmp_path):
    output = write_operation_body(
        tmp_path,
        "G0 A0\nM30\n",
        body_start=0,
        tail_start=1,
        rotationLine=0,
        rotationAngle=-12.5,
        preserveRotation=False,
        settings=writer_settings(safeYRetraction=False),
    )

    assert output == (
        "(Rotating a-axis between setups)\n"
        "G90 G53 G0 Z-3\n"
        "G90 G54 G0 A-12.5\n"
    )


def test_write_body_restores_rapid_move_and_removes_feed(tmp_path):
    output = write_operation_body(
        tmp_path,
        "G1 Z5 F100\nX30\nZ0\nM30\n",
        body_start=0,
        tail_start=3,
        rapidsAnalysis={1: {"endLine": 3, "startHasFeed": True}},
    )

    assert output == (
        "G0 Z5 (Rapid movement start)\n"
        "X30\n"
        "Z0\n"
        "G1 (Rapid movement end)\n"
    )
