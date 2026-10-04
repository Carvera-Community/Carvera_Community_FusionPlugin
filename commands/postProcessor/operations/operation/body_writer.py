import re
from dataclasses import dataclass
from typing import TextIO

from .operation_context import OperationContext
from .analysis import parsed_operation

from ...file_modes import FileModes

_A_WORD_RE = re.compile(r"(?<![A-Za-z])A(-?\d+(?:\.\d*)?)", re.IGNORECASE)

def _find_a_word(line: str) -> re.Match[str] | None:
    """Find the A word in the code part of a line, wherever it sits among the other words."""
    return _A_WORD_RE.search(line.split("(", 1)[0])

@dataclass(frozen=True)
class BodyWriterSettings:
    safeYRetraction: bool
    yRetractionCoordinate: float

    @classmethod
    def from_processing_settings(cls, settings) -> "BodyWriterSettings":
        return cls(settings.safeYRetraction, settings.yRetractionCoordinate)

def write_body(
    ctx: OperationContext,
    fileHandle: TextIO,
    settings: BodyWriterSettings | None = None,
):
    analysis = parsed_operation(ctx)
    if settings is None:
        if ctx.processingSettings is None:
            raise ValueError("Body writer settings are required")
        settings = BodyWriterSettings.from_processing_settings(ctx.processingSettings)

    def _strip_feed(line: str) -> str:
        # Preserve newline exactly as it was
        hasNewline = line.endswith("\n")
        s = line[:-1] if hasNewline else line

        # If you allow comments like "(...)" and want to avoid touching inside them:
        commentStart = s.find("(")
        if commentStart >= 0:
            prefix = s[:commentStart]
            suffix = s[commentStart:]
        else:
            prefix = s
            suffix = ""

        # Remove feed(s) from the non-comment part
        prefix = ctx.remove_feed_from_line(prefix)

        out = (prefix + (" " if (prefix and suffix and not suffix.startswith(" ")) else "") + suffix).rstrip()
        return out + ("\n" if hasNewline else "")

    def _match_line(line: str, row: int) -> bool:
        lineMatch = ctx.match_line(line)
        if lineMatch:
            if lineMatch.group("G") is not None:
                gCode = lineMatch.group("G")
                if lineMatch.group("A") is not None:
                    aCode = lineMatch.group("A")
                    if float(aCode) == 0.0:
                        if float(gCode) == 0.0:
                            # Special handling of A-axis rotation moves.
                            # Operations are generated one by one, so the generated
                            # rotation is always to the setup angle (A0).
                            return row != analysis.rotation_line or _handle_rotation()
                        elif float(gCode) == 92.4:
                            if lineMatch.group("R") is not None:
                                # The post processor puts the program shrink in the
                                # tail. Since the shared tail is written once per
                                # result file, every shrink found in an operation
                                # body must be stripped.
                                return True
        return False

    def _write_rotation(angle: float) -> None:
        ctx.write_line(fileHandle, "(Rotating a-axis between setups)")
        # Using G53 for absolute machine coordinates for safe retraction
        if settings.safeYRetraction:
            ctx.write_line(fileHandle, "G90 G53 G0 Z-3 Y{yRetraction}".format(yRetraction = settings.yRetractionCoordinate))
        else:
            ctx.write_line(fileHandle, "G90 G53 G0 Z-3")
        ctx.write_line(fileHandle, "G90 G54 G0 A{angle}".format(angle = f"{angle:.3f}".rstrip("0").rstrip(".")))
        ctx.aAngle = 0.0 # The generated moves treat the setup angle as A0

    def _handle_rotation() -> bool:
        if ctx.preserveRotation: # We will use the already generated gcode.
            return False
        if ctx.rotationAngle is not None: # Write our own rotation code based on the provided rotation angle
            _write_rotation(ctx.rotationAngle)
        elif ctx.aAngle % 360 != 0.0: # An earlier operation left the A axis away from the setup angle (e.g. a pattern), so rotate back.
            _write_rotation(ctx.setupAngle)
        return True

    if analysis.body is None:
        return

    with analysis.source_file.open(FileModes.READ) as operationFile:
        line = operationFile.readline()
        row = 0
        rapidsEnds = 0
        readNextLine = False
        while len(line) != 0:
            if readNextLine:
                line = operationFile.readline() 
                row += 1
                readNextLine = False
                if len(line) == 0 or not analysis.body.contains(row):
                    break

            if analysis.body.contains(row):
                if row == analysis.body.start: # Add an extra line marking where this operation starts
                    if analysis.allow_blank_lines:
                        ctx.write(fileHandle, '\n') # keep blank line before operation start
                rapid_rewrite = analysis.rapid_rewrite_at(row + 1)
                if rapid_rewrite is not None: # Add rapids comments if this line is the start of a rapid move
                    rapidsEnds = rapid_rewrite.end_line
                    startHasFeed = rapid_rewrite.start_has_feed
                    lineMatch = ctx.match_line(line)
                    if lineMatch:
                        if startHasFeed: 
                            line = _strip_feed(line)
                        if lineMatch.group("G") is not None:
                            if int(lineMatch.group("G")) == 1:
                                gStart, gEnd = lineMatch.span("G")
                                line = (line[:gStart] + "0" + line[gEnd:]).rstrip() + " (Rapid movement start)\n" # Change G1 to G0 for rapid move comment line
                        else:
                            ctx.write_line(fileHandle, f"G0 {line.rstrip()} (Rapid movement start)")
                            readNextLine = True
                            continue
                if row + 1 == rapidsEnds:
                    rapidsEnds = 0
                    ctx.write(fileHandle, line)
                    line = "G1 (Rapid movement end)\n" # Add a line after the rapid move to switch back to G1 if it was changed for the rapid move comment
                if _match_line(line, row):
                    readNextLine = True
                    continue

                aWord = _find_a_word(line)
                if aWord:
                    ctx.aAngle = float(aWord.group(1))
                    if ctx.setupAngle != 0.0: # The generated A moves are relative to the setup angle, so shift them onto it.
                        start, end = aWord.span(1)
                        line = line[:start] + f"{ctx.aAngle + ctx.setupAngle:.3f}".rstrip("0") + line[end:]
                ctx.write(fileHandle, line)

            line = operationFile.readline()
            row += 1
            if row >= analysis.body.start and not analysis.body.contains(row):
                break
