from pathlib import Path
from types import SimpleNamespace

from addin_import import import_addin_module


module = import_addin_module(
    "commands.postProcessor.operations.operation.analysis"
)
LineRange = module.LineRange
ParsedOperation = module.ParsedOperation


def test_line_range_uses_a_stop_exclusive_boundary():
    lines = LineRange(2, 5)

    assert not lines.contains(1)
    assert lines.contains(2)
    assert lines.contains(4)
    assert not lines.contains(5)


def test_parsed_operation_converts_legacy_sentinels_and_rapid_metadata():
    context = SimpleNamespace(
        tempFilePath=Path("operation.nc"),
        headerEndLine=3,
        bodyStartLine=4,
        tailStartLine=10,
        toolCommentLine=-1,
        rotationLine=6,
        shrinkLine=-1,
        allowBlankLines=True,
        rapidsAnalysis={5: {"endLine": 8, "startHasFeed": True}},
    )

    parsed = ParsedOperation.from_context(context)

    assert parsed.header == LineRange(0, 4)
    assert parsed.body == LineRange(4, 10)
    assert parsed.tail == LineRange(10)
    assert parsed.tool_comment_line is None
    assert parsed.rapid_rewrite_at(5).end_line == 8


def test_missing_tail_produces_an_open_ended_body_range():
    context = SimpleNamespace(
        tempFilePath=Path("manual.nc"),
        headerEndLine=0,
        bodyStartLine=1,
        tailStartLine=-1,
        toolCommentLine=-1,
        rotationLine=-1,
        shrinkLine=-1,
        allowBlankLines=False,
        rapidsAnalysis=None,
    )

    assert ParsedOperation.from_context(context).body == LineRange(1)
