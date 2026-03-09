from pathlib import Path

from .operation_context import OperationContext

from .rapidsParser import RapidsParser

from ...settings.settings import Settings

def parseFile(ctx: OperationContext):
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
                    if f"G{headerMatch.group('G')}" in Settings.Get(Settings.HEADER_END_CODES):
                        # Found the end of the header
                        ctx.headerEndLine = lineNumber
                        return (True, True)
                    elif inHeader: # Found a g-code that isn't in the header end codes, so we're in the body.
                        ctx.bodyStartLine = lineNumber
                        return (False, inHeader) 

                if headerMatch.group("M") is not None:
                    # Found an m-code, check if it is in the list of
                    # header end codes
                    if f"M{headerMatch.group('M')}" in Settings.Get(Settings.HEADER_END_CODES):
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
                gCode = int(bodyMatch.group("G"))
                if gCode == 0:
                    lineMatch = ctx.lineWriter._PARSE_LINE_RE.match(line)
                    # We're only interested in the first rotation move
                    if not ctx.hasRotation and lineMatch and lineMatch.group("G") is not None and lineMatch.group("A") is not None:
                        aCode = float(lineMatch.group("A"))
                        if aCode == 0.0:
                            # Found A-axis rotation move
                            ctx.rotationLine = lineNumber
            if bodyMatch.group("T") is not None and ctx.bodyStartLine == -1:
                # found body start
                ctx.bodyStartLine = lineNumber
            elif bodyMatch.group("M") is not None:
                mCode = int(bodyMatch.group("M"))
                if f"M{mCode}" in Settings.Get(Settings.END_CODES):
                    # found tail start
                    ctx.tailStartLine = lineNumber
                    return True # File analysis complete
        return False

    if Settings(Settings.RESTORE_RAPID_MOVES):
        minDist = Settings(Settings.RAPID_MOVES_MINIMUM_DISTANCE) | 20
        maxStepsInbetween = Settings(Settings.RAPID_MOVES_MAX_STEPS) | 3
        ctx.rapidsAnalysis = {segment["startLine"]: { 
            "endLine": segment["endLine"], 
            "startHasFeed": segment["startHasFeed"]}
                for segment in RapidsParser().analyze(RapidsParser().parseFile(ctx.tempFilePath, maxStepsInbetween = maxStepsInbetween), minDist = minDist)
                if segment.get("isValid") and "startLine" in segment and "endLine" in segment and "startHasFeed" in segment }
    
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
