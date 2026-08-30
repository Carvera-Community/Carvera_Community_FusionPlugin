from dataclasses import dataclass
from pathlib import Path

from .operation_context import OperationContext

from .rapidsParser import RapidsParser

from ...settings.settings import Settings


@dataclass(frozen=True)
class ParserSettings:
    headerEndCodes: str
    endCodes: str
    restoreRapidMoves: bool
    rapidMovesMinimumDistance: float
    rapidMovesMaxSteps: int

    @classmethod
    def fromProcessingSettings(cls, settings) -> "ParserSettings":
        return cls(
            headerEndCodes=settings.headerEndCodes,
            endCodes=settings.endCodes,
            restoreRapidMoves=settings.restoreRapidMoves,
            rapidMovesMinimumDistance=settings.rapidMovesMinimumDistance,
            rapidMovesMaxSteps=settings.rapidMovesMaxSteps,
        )

    @classmethod
    def fromCurrentSettings(cls) -> "ParserSettings":
        minimumDistance = Settings.Get(Settings.RAPID_MOVES_MINIMUM_DISTANCE)
        maximumSteps = Settings.Get(Settings.RAPID_MOVES_MAX_STEPS)
        return cls(
            headerEndCodes=Settings.Get(Settings.HEADER_END_CODES) or "",
            endCodes=Settings.Get(Settings.END_CODES) or "",
            restoreRapidMoves=bool(Settings.Get(Settings.RESTORE_RAPID_MOVES)),
            rapidMovesMinimumDistance=20 if minimumDistance is None else minimumDistance,
            rapidMovesMaxSteps=3 if maximumSteps is None else maximumSteps,
        )


def parseFile(ctx: OperationContext, settings: ParserSettings | None = None):
    settings = settings or (
        ParserSettings.fromProcessingSettings(ctx.processingSettings)
        if ctx.processingSettings is not None
        else ParserSettings.fromCurrentSettings()
    )
    #region Header example
    # Find the start of the header and body in the generated file

    # Parse the gcode. We expect a header like this:
    #
    # % <optional>
    # Oxxxx <optional>
    # (<comments>) <0 or more lines>
    # (<Txx tool comment>) <optional>
    # <comments or G-code initialization, up to Txx>
    #
    # This header is stripped from all files after the first,
    # except the tool comment is put in a list at the top.
    # The header ends when we find the body, which starts with:
    #
    # Txx ...   (optionally preceded by line number Nxx)
    #
    # We copy all the body, looking for the tail. The start
    # of the tail is denoted by any of a list of G-codes
    # entered by the user. The defaults are:
    # M30 - end program
    # M5 - stop spindle
    # M9 - stop coolant
    # The tail is stripped until the last operation is done.
    #endregion

    def _parseHeaderLine(line: str, lineNumber: int, inHeader: bool) -> tuple[bool, bool]:
        toolComment = ctx.lineWriter._TOOL_COMMENT_REG.search(line)
        if toolComment: # We have found the tool comment line
            ctx.toolCommentLine = lineNumber
            return True, inHeader
        else:
            headerMatch = ctx.lineWriter._BODY_RE.match(line)
            if headerMatch:
                if headerMatch.group("G") is not None:
                    # Found a g-code, check if it is in the list of
                    # header end codes
                    if f"G{headerMatch.group('G')}" in settings.headerEndCodes:
                        # Found the end of the header
                        ctx.headerEndLine = lineNumber
                        return (True, True)
                    elif inHeader: # Found a g-code that isn't in the header end codes, so we're in the body.
                        ctx.bodyStartLine = lineNumber
                        return (False, inHeader) 

                if headerMatch.group("M") is not None:
                    # Found an m-code, check if it is in the list of
                    # header end codes
                    if f"M{headerMatch.group('M')}" in settings.headerEndCodes:
                        # Found the end of the header
                        ctx.headerEndLine = lineNumber
                        return (True, True)
                    elif inHeader: # Found an m-code that isn't in the header end codes, so we're done with the header.
                        ctx.bodyStartLine = lineNumber
                        return (False, inHeader) 

                if headerMatch.group("T") is not None:
                    # Definitely found the body as this is either a 
                    # tool change line or a line not in header end 
                    # codes (which matched earlier), so we're done
                    ctx.bodyStartLine = lineNumber
                    if ctx.headerEndLine == -1: 
                        ctx.headerEndLine = lineNumber - 1 # Definite end of header
                    return (False, inHeader)
                
                if (headerMatch.group("line") is not None 
                    and headerMatch.group("line") == f"({ctx.name})\n"):
                        # This is a comment line with the operation name, ignore it
                        # but use it as a possible end of the header.
                        ctx.headerEndLine = lineNumber -1
                        return (True, inHeader)
                
            return (not inHeader, inHeader)

    def _parseBodyLine(line: str, lineNumber: int):
        bodyMatch = ctx.lineWriter._BODY_RE.match(line)
        if bodyMatch:
            if bodyMatch.group("G") is not None:
                gCode = float(bodyMatch.group("G"))
                if gCode in [0, 92.4]:
                    lineMatch = ctx.lineWriter._PARSE_LINE_RE.match(line)
                    if lineMatch \
                        and lineMatch.group("G") is not None \
                        and lineMatch.group("A") is not None:

                        if gCode == 0:
                            # We're only interested in the first rotation move
                            if not ctx.hasRotation:
                                aCode = float(lineMatch.group("A"))
                                if aCode == 0.0:
                                    # Found A-axis rotation move
                                    ctx.rotationLine = lineNumber
                        elif gCode == 92.4:
                            # Find out if this is a shrink line (G92.4 A0 R0)
                            if not ctx.hasShrink \
                                and lineMatch.group("R") is not None:
                                ctx.shrinkLine = lineNumber
                        
            if bodyMatch.group("T") is not None and ctx.bodyStartLine == -1:
                # found body start
                ctx.bodyStartLine = lineNumber
            elif bodyMatch.group("M") is not None:
                mCode = int(bodyMatch.group("M"))
                if f"M{mCode}" in settings.endCodes:
                    # found tail start
                    ctx.tailStartLine = lineNumber
                    return True # File analysis complete
        return False

    if settings.restoreRapidMoves:
        ctx.rapidsAnalysis = {seg["startLine"]: { 
            "endLine": seg["endLine"], 
            "startHasFeed": seg["startHasFeed"]}
                for seg in RapidsParser().analyze(
                    RapidsParser().parseFile(
                        ctx.tempFilePath,
                        maxStepsInbetween=settings.rapidMovesMaxSteps,
                    ),
                    minDist=settings.rapidMovesMinimumDistance,
                )
                if seg.get("isValid") and "startLine" in seg and "endLine" in seg}
    
    with ctx.tempFilePath.open("r") as operationFile:
        line = operationFile.readline()
        ctx.toolCommentLine = -1
        lineNumber = -1
        inHeader = False
        processHeader = True
        processBody = False
        while len(line) != 0:
            lineNumber += 1

            if not ctx.allowBlankLines and line[0] == "\n":
                ctx.allowBlankLines = True

            if processHeader:
                processHeader, inHeader = _parseHeaderLine(line, lineNumber, inHeader)
                processBody = not processHeader
            elif processBody:
                if _parseBodyLine(line, lineNumber):
                    return
            line = operationFile.readline()
    return # No tail found, so possibly a handmade operation
