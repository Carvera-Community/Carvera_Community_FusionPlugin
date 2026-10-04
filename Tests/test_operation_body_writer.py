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
write_body = body_writer.write_body
ProcessingSettings = import_addin_module(
    "commands.postProcessor.processing_settings"
).ProcessingSettings
Settings = import_addin_module(
    "commands.postProcessor.settings.settings"
).Settings


def writer_settings(**overrides) -> BodyWriterSettings:
    values = {
        "safeYRetraction": True,
        "yRetractionCoordinate": -100,
    }
    values.update(overrides)
    return BodyWriterSettings(**values)


def test_operation_context_instances_have_independent_line_writers():
    first = OperationContext(0)
    second = OperationContext(1)

    assert first.lineWriter is not second.lineWriter
    assert first.tempFilePath == Path()
    assert second.tempFilePath == Path()


def test_body_writer_uses_captured_retraction_settings(tmp_path):
    Settings._items = dict(Settings._default_settings)
    Settings._items[Settings.SAFE_Y_RETRACTION] = False
    snapshot = ProcessingSettings.capture()
    Settings._items[Settings.SAFE_Y_RETRACTION] = True
    context = OperationContext(0, processingSettings=snapshot)
    context.tempFilePath = tmp_path / "operation.nc"
    context.tempFilePath.write_text("G0 A0\nM30\n", encoding="utf-8")
    context.bodyStartLine = 0
    context.tailStartLine = 1
    context.rotationLine = 0
    context.rotationAngle = 10

    output = StringIO()
    write_body(context, output)

    assert "G90 G53 G0 Z-3\n" in output.getvalue()
    assert " Y" not in output.getvalue()


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
    write_body(context, output, settings or writer_settings())
    return output.getvalue()


def test_write_body_streams_only_body_rows(tmp_path):
    output = write_operation_body(
        tmp_path,
        "(Header)\nT1 M6\nG1 X10\nG1 X20\nM30\n",
        body_start=1,
        tail_start=4,
    )

    assert output == "T1 M6\nG1 X10\nG1 X20\n"


def test_write_body_streams_to_eof_when_no_tail_was_detected(tmp_path):
    output = write_operation_body(
        tmp_path,
        "(Header)\nG1 X10\nG1 X20\n",
        body_start=1,
        tail_start=-1,
    )

    assert output == "G1 X10\nG1 X20\n"


def test_write_body_removes_shrink_from_operation_body(tmp_path):
    output = write_operation_body(
        tmp_path,
        "T1 M6\nG92.4 A0 R0\nG1 X10\nM30\n",
        body_start=0,
        tail_start=3,
        shrinkLine=1,
    )

    assert output == "T1 M6\nG1 X10\n"


def test_write_body_removes_shrink_even_when_operation_was_marked_final(tmp_path):
    output = write_operation_body(
        tmp_path,
        "T1 M6\nG92.4 A0 R0\nG1 X10\nM30\n",
        body_start=0,
        tail_start=3,
        shrinkLine=1,
        isLastOp=True,
    )

    assert output == "T1 M6\nG1 X10\n"


def test_write_body_retracts_and_rotates_back_when_a_axis_is_not_at_setup_angle(tmp_path):
    output = write_operation_body(
        tmp_path,
        "T1 M6\nG0 A0\nG1 X10\nM30\n",
        body_start=0,
        tail_start=3,
        rotationLine=1,
        aAngle=334.286,
        setupAngle=55.714,
    )

    assert output == (
        "T1 M6\n"
        "(Rotating a-axis between setups)\n"
        "G90 G53 G0 Z-3 Y-100\n"
        "G90 G54 G0 A55.714\n"
        "G1 X10\n"
    )


def test_write_body_offsets_pattern_angles_by_setup_angle(tmp_path):
    output = write_operation_body(
        tmp_path,
        "T1 M6\nG92.4 A120 R0 (shrink)\nG0 A120.\nG1 X10 Z3 A11 F300\nM30\n",
        body_start=0,
        tail_start=4,
        setupAngle=55.714,
    )

    assert output == (
        "T1 M6\nG92.4 A175.714 R0 (shrink)\nG0 A175.714\nG1 X10 Z3 A66.714 F300\n"
    )


def test_write_body_strips_rotation_when_a_axis_is_a_whole_number_of_turns_away(tmp_path):
    output = write_operation_body(
        tmp_path,
        "T1 M6\nG0 A0\nG1 X10\nM30\n",
        body_start=0,
        tail_start=3,
        rotationLine=1,
        aAngle=720.0,
    )

    assert output == "T1 M6\nG1 X10\n"


def test_write_body_strips_rotation_in_later_operation_of_rotated_setup(tmp_path):
    source = tmp_path / "operation.nc"
    source.write_text("T1 M6\nG0 A0\nG1 X10\nM30\n", encoding="utf-8")
    first = OperationContext(0)
    second = OperationContext(1)
    for context in (first, second):
        context.tempFilePath = source
        context.bodyStartLine = 0
        context.tailStartLine = 3
        context.rotationLine = 1
    first.rotationAngle = 30.0
    write_body(first, StringIO(), writer_settings())
    second.aAngle = first.aAngle

    output = StringIO()
    write_body(second, output, writer_settings())

    assert output.getvalue() == "T1 M6\nG1 X10\n"


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
