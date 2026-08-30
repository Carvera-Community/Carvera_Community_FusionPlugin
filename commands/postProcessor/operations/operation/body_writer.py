from pathlib import Path
import re
from typing import Any, TextIO

from .operation_context import OperationContext

from ...file_modes import FileModes
from ...settings.settings import Settings

def writeBody(ctx: OperationContext, fileHandle: TextIO):

    def _stripFeed(line: str) -> str:
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
        prefix = ctx.removeFeedFromLine(prefix)

        out = (prefix + (" " if (prefix and suffix and not suffix.startswith(" ")) else "") + suffix).rstrip()
        return out + ("\n" if hasNewline else "")

    def _matchLine(line: str, row: int) -> bool:
        lineMatch = ctx.matchLine(line)
        if lineMatch:
            if lineMatch.group("G") is not None:
                gCode = lineMatch.group("G")
                if lineMatch.group("A") is not None:
                    aCode = lineMatch.group("A")
                    if float(aCode) == 0.0:
                        if float(gCode) == 0.0:
                            # Special handling of A-axis rotation moves.
                            # The rotation should always be 0 as the 
                            # operations are always generated one by one
                            return row != ctx.rotationLine or _handleRotation()
                        elif float(gCode) == 92.4:
                            if lineMatch.group("R") is not None and not ctx.isLastOp:
                                # Strip out all shrink A-axis commands unless it is the last operation in the file
                                return row != ctx.shrinkLine
        return False

    def _handleRotation() -> bool:
        if ctx.rotationAngle is None: # No rotation provided, do not preserve the line as it will rotate to 0 which we don't want.
            return not ctx.preserveRotation
        else: # Write our own rotation code based on the provided rotation angle
            if ctx.preserveRotation: # We will use the already generated gcode.
                return False
            # Adding our own rotation gcodes
            ctx.writeLine(fileHandle, "(Rotating a-axis between setups)")
            # Using G53 for absolute machine coordinates for safe retraction
            if Settings(Settings.SAFE_Y_RETRACTION):
                ctx.writeLine(fileHandle, "G90 G53 G0 Z-3 Y{yRetraction}".format(yRetraction = Settings(Settings.Y_RETRACTION_COORDINATE)))
            else:
                ctx.writeLine(fileHandle, "G90 G53 G0 Z-3")
            ctx.writeLine(fileHandle, "G90 G54 G0 A{angle}".format(angle = f"{ctx.rotationAngle:.3f}".rstrip("0").rstrip(".")))
            return True

    with ctx.tempFilePath.open(FileModes.READ) as operationFile:
        line = operationFile.readline()
        row = 0
        rapidsEnds = 0
        readNextLine = False
        while len(line) != 0:
            if readNextLine:
                line = operationFile.readline() 
                row += 1
                readNextLine = False

            if row >= ctx.bodyStartLine:
                if row == ctx.bodyStartLine: # Add an extra line marking where this operation starts
                    if ctx.allowBlankLines:
                        ctx.write(fileHandle, '\n') # keep blank line before operation start
                if ctx.rapidsAnalysis and row + 1 in ctx.rapidsAnalysis: # Add rapids comments if this line is the start of a rapid move
                    rapidsEnds = ctx.rapidsAnalysis[row + 1]["endLine"]
                    startHasFeed = ctx.rapidsAnalysis[row + 1]["startHasFeed"]
                    lineMatch = ctx.matchLine(line)
                    if lineMatch:
                        if startHasFeed: 
                            line = _stripFeed(line)
                        if lineMatch.group("G") is not None:
                            if int(lineMatch.group("G")) == 1:
                                gStart, gEnd = lineMatch.span("G")
                                line = (line[:gStart] + "0" + line[gEnd:]).rstrip() + " (Rapid movement start)\n" # Change G1 to G0 for rapid move comment line
                        else:
                            ctx.writeLine(fileHandle, f"G0 {line.rstrip()} (Rapid movement start)")
                            readNextLine = True
                            continue
                if row + 1 == rapidsEnds:
                    rapidsEnds = 0
                    ctx.write(fileHandle, line)
                    line = "G1 (Rapid movement end)\n" # Add a line after the rapid move to switch back to G1 if it was changed for the rapid move comment
                if _matchLine(line, row):
                    readNextLine = True
                    continue

                ctx.write(fileHandle, line)

            line = operationFile.readline()
            row += 1
            if row >= ctx.tailStartLine:                            
                break
