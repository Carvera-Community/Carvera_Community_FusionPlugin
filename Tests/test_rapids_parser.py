from pathlib import Path

import pytest

from commands.postProcessor.operations.operation.rapidsParser import MOTIONS, RapidsParser


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
