from pathlib import Path

import pytest

from addin_import import import_addin_module


rapids_parser = import_addin_module(
    "commands.postProcessor.operations.operation.rapidsParser"
)
MOTIONS = rapids_parser.MOTIONS
RapidsParser = rapids_parser.RapidsParser


def write_operation(tmp_path: Path, contents: str) -> Path:
    path = tmp_path / "operation.nc"
    path.write_text(contents, encoding="utf-8")
    return path


def test_parse_line_recognizes_motion_and_ignores_comments():
    result = RapidsParser._parseLine("g01 X1.5 Y-2 F100 (Z99 G3)")

    assert result.localMotion == MOTIONS.G1
    assert result.sawX
    assert result.sawY
    assert not result.sawZ
    assert result.words == [("G", 1.0), ("X", 1.5), ("Y", -2.0), ("F", 100.0)]


def test_parse_file_finds_z_up_xy_z_down_segment(tmp_path):
    path = write_operation(tmp_path, "G1 Z0\nG1 Z5\nX30\nZ0\n")

    segments = RapidsParser.parseFile(path)

    assert len(segments) == 1
    segment = segments[0]
    assert segment.startLineNumber == 2
    assert segment.endLineNumber == 4
    assert segment.middleLineNumbers == [3]
    assert segment.totalXYDistance == 30.0
    assert segment.deltaZUp == 5.0
    assert segment.deltaZDown == 5.0


def test_parse_file_rejects_negative_step_limit(tmp_path):
    path = write_operation(tmp_path, "")

    with pytest.raises(ValueError, match="maxStepsInbetween"):
        RapidsParser.parseFile(path, maxStepsInbetween=-1)


def test_analysis_marks_qualifying_segment_valid(tmp_path):
    path = write_operation(tmp_path, "G1 Z0\nG1 Z5 F100\nX30\nZ0\n")
    segments = RapidsParser.parseFile(path)

    analysis = list(RapidsParser.analyze(segments, minDist=10))

    assert len(analysis) == 1
    assert analysis[0]["isValid"]
    assert analysis[0]["startHasFeed"]
    assert analysis[0]["startLine"] == 2
    assert analysis[0]["endLine"] == 4


def test_analysis_uses_greater_of_xy_and_z_distance(tmp_path):
    path = write_operation(tmp_path, "G1 Z0\nG1 Z5\nX30\nZ0\n")
    segments = RapidsParser.parseFile(path)

    analysis = list(RapidsParser.analyze(segments, minDist=25))

    assert len(analysis) == 1
    assert analysis[0]["isValid"]


def test_analysis_rejects_feed_in_middle_move(tmp_path):
    path = write_operation(tmp_path, "G1 Z0\nG1 Z5\nX30 F100\nZ0\n")

    analysis = list(RapidsParser.analyze(RapidsParser.parseFile(path), minDist=10))

    assert len(analysis) == 1
    assert not analysis[0]["isValid"]


def test_analysis_rejects_arc_in_middle_move(tmp_path):
    path = write_operation(tmp_path, "G1 Z0\nG1 Z5\nG2 X30\nG1 Z0\n")
    segments = RapidsParser.parseFile(path, requireG1=False)

    analysis = list(RapidsParser.analyze(segments, minDist=10))

    assert len(analysis) == 1
    assert not analysis[0]["isValid"]


def test_analysis_moves_end_before_feed_line(tmp_path):
    path = write_operation(tmp_path, "G1 Z0\nG1 Z5\nX30\nZ0 F100\n")

    analysis = list(RapidsParser.analyze(RapidsParser.parseFile(path), minDist=10))

    assert analysis == [{
        "startLine": 2,
        "endLine": 3,
        "startHasFeed": False,
        "isValid": True,
    }]


def test_analysis_rejects_short_effective_distance(tmp_path):
    path = write_operation(tmp_path, "G1 Z0\nG1 Z1\nX2\nZ0\n")

    analysis = list(RapidsParser.analyze(RapidsParser.parseFile(path), minDist=10))

    assert len(analysis) == 1
    assert not analysis[0]["isValid"]
