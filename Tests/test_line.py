from io import StringIO

from commands.postProcessor.line import Line


def test_parse_line_recognizes_decimal_gcode_and_r_parameter():
    match = Line._PARSE_LINE_RE.match("G92.4 A0 R0")

    assert match is not None
    assert match.group("G") == "92.4"
    assert match.group("A") == "0"
    assert match.group("R") == "0"


def test_parse_line_reports_missing_r_parameter():
    match = Line._PARSE_LINE_RE.match("G0 A0")

    assert match is not None
    assert match.group("G") == "0"
    assert match.group("A") == "0"
    assert match.group("R") is None


def test_body_expression_preserves_decimal_gcode():
    match = Line._BODY_RE.match("N10 G92.4 A0 R0\n")

    assert match is not None
    assert match.group("N") == "N10 "
    assert match.group("G") == "92.4"


def test_write_removes_leading_line_number():
    output = StringIO()

    Line.write(output, "N105 G1 X2.5\n")

    assert output.getvalue() == " G1 X2.5\n"


def test_remove_feed_does_not_remove_comment_text():
    line = "G1 X10 F250 (keep F999)"

    assert Line.removeFeedFromLine(line) == "G1 X10  (keep F999)"
