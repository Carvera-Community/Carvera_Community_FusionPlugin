from pathlib import Path

from addin_import import import_addin_module


OperationContext = import_addin_module(
    "commands.postProcessor.operations.operation.operation_context"
).OperationContext
parser = import_addin_module("commands.postProcessor.operations.operation.parser")
ParserSettings = parser.ParserSettings
parseFile = parser.parseFile


def parser_settings(**overrides) -> ParserSettings:
    values = {
        "headerEndCodes": "G20\nG21",
        "endCodes": "M5\nM9\nM30",
        "restoreRapidMoves": False,
        "rapidMovesMinimumDistance": 20,
        "rapidMovesMaxSteps": 3,
    }
    values.update(overrides)
    return ParserSettings(**values)


def parse_operation(tmp_path: Path, contents: str, **setting_overrides):
    path = tmp_path / "operation.nc"
    path.write_text(contents, encoding="utf-8")
    context = OperationContext(0)
    context.name = "Operation"
    context.tempFilePath = path
    parseFile(context, parser_settings(**setting_overrides))
    return context


def test_parse_file_finds_header_body_rotation_shrink_and_tail(tmp_path):
    context = parse_operation(
        tmp_path,
        "(Header)\nG21\n(T1 Tool)\nT1 M6\nG0 A0\nG92.4 A0 R0\nG1 X10\nM30\n",
    )

    assert context.headerEndLine == 1
    assert context.toolCommentLine == 2
    assert context.bodyStartLine == 3
    assert context.rotationLine == 4
    assert context.shrinkLine == 5
    assert context.tailStartLine == 7


def test_parse_file_uses_explicit_header_and_tail_codes(tmp_path):
    context = parse_operation(
        tmp_path,
        "(Header)\nG90\nT1 M6\nG1 X10\nM2\n",
        headerEndCodes="G90",
        endCodes="M2",
    )

    assert context.headerEndLine == 1
    assert context.bodyStartLine == 2
    assert context.tailStartLine == 4


def test_parse_file_keeps_first_rotation_and_shrink(tmp_path):
    context = parse_operation(
        tmp_path,
        "G21\nT1 M6\nG0 A0\nG0 A0\nG92.4 A0 R0\nG92.4 A0 R0\nM30\n",
    )

    assert context.rotationLine == 2
    assert context.shrinkLine == 4


def test_parse_file_ignores_shrink_without_r_parameter(tmp_path):
    context = parse_operation(
        tmp_path,
        "G21\nT1 M6\nG92.4 A0\nM30\n",
    )

    assert context.shrinkLine == -1


def test_parse_file_restores_qualifying_rapid_move(tmp_path):
    context = parse_operation(
        tmp_path,
        "G21\nT1 M6\nG1 Z0\nG1 Z5 F100\nX30\nZ0\nM30\n",
        restoreRapidMoves=True,
        rapidMovesMinimumDistance=25,
    )

    assert context.rapidsAnalysis == {
        4: {"endLine": 6, "startHasFeed": True},
    }
