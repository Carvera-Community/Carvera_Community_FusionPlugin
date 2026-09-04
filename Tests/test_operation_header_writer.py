from pathlib import Path

from addin_import import import_addin_module


OperationContext = import_addin_module(
    "commands.postProcessor.operations.operation.operation_context"
).OperationContext
header_writer = import_addin_module(
    "commands.postProcessor.operations.operation.header_writer"
)
HeaderWriterSettings = header_writer.HeaderWriterSettings


def header_settings(**overrides) -> HeaderWriterSettings:
    values = {
        "restoreRapidMoves": False,
        "rapidMovesMaxSteps": 3,
        "rapidMovesMinimumDistance": 20,
    }
    values.update(overrides)
    return HeaderWriterSettings(**values)


def operation_context(tmp_path: Path) -> OperationContext:
    source = tmp_path / "temporary.nc"
    source.write_text(
        "(temporary)\n(Header comment)\n(T7 Tool description)\nG21\nT7 M6\n",
        encoding="utf-8",
    )
    context = OperationContext(0)
    context.tempFilePath = source
    context.toolCommentLine = 2
    context.headerEndLine = 3
    return context


def read_written_output(tmp_path: Path, writer) -> str:
    output_path = tmp_path / "result.nc"
    with output_path.open("w", encoding="utf-8") as output:
        writer(output)
    return output_path.read_text(encoding="utf-8")


def test_write_header_start_replaces_temporary_name(tmp_path):
    context = operation_context(tmp_path)

    output = read_written_output(
        tmp_path,
        lambda file_handle: header_writer.write_header_start(
            context, file_handle, header_settings()
        ),
    )

    assert output.startswith("(result)\n(Generated with ")
    assert "(temporary)" not in output
    assert output.endswith("(Header comment)\n")


def test_write_header_start_describes_rapid_restoration(tmp_path):
    context = operation_context(tmp_path)

    output = read_written_output(
        tmp_path,
        lambda file_handle: header_writer.write_header_start(
            context,
            file_handle,
            header_settings(
                restoreRapidMoves=True,
                rapidMovesMaxSteps=5,
                rapidMovesMinimumDistance=42,
            ),
        ),
    )

    assert (
        "(Restore rapid moves enabled: True, maximum steps inbetween start and "
        "stop: 5, minimum travel distance: 42mm)\n"
    ) in output


def test_write_tool_comment_copies_only_detected_comment(tmp_path):
    context = operation_context(tmp_path)

    output = read_written_output(
        tmp_path,
        lambda file_handle: header_writer.write_tool_comment(context, file_handle),
    )

    assert output == "(T7 Tool description)\n"


def test_write_header_end_copies_rows_after_tool_comment(tmp_path):
    context = operation_context(tmp_path)

    output = read_written_output(
        tmp_path,
        lambda file_handle: header_writer.write_header_end(context, file_handle),
    )

    assert output == "G21\n"


def test_write_header_combines_all_header_sections(tmp_path):
    context = operation_context(tmp_path)

    output = read_written_output(
        tmp_path,
        lambda file_handle: header_writer.write_header(
            context, file_handle, header_settings()
        ),
    )

    assert "(Header comment)\n(T7 Tool description)\nG21\n" in output
