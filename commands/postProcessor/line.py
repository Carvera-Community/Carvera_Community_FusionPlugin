
import re
from typing import Final, TextIO

from .settings import Settings

class Line():

    _BODY_RE: Final = re.compile(r""
        r"(?P<N>N[0-9]+ *)?" # line number
        r"(?P<line>"         # line w/o number
        r"(M(?P<M>[0-9]+) *)?" # M-code
        r"(G(?P<G>[0-9]+) *)?" # G-code
        r"(T(?P<T>[0-9]+))?" # Tool
        r".+)",              # to end of line
        re.IGNORECASE | re.DOTALL)

    _PARSE_LINE_RE: Final = re.compile(r""
            r"(G(?P<G>[0-9]+(\.[0-9]*)?)[^XYZFA]*)?"
            r"(?P<XY>((X-?[0-9]+(\.[0-9]*)?)[^XYZFA]*)?((Y-?[0-9]+(\.[0-9]*)?)[^XYZFA]*)?)"
            r"(A(?P<A>-?[0-9]+(\.[0-9]*)?)[^XYZFA]*)?"
            r"(Z(?P<Z>-?[0-9]+(\.[0-9]*)?)[^XYZFA]*)?"
            r"(F(?P<F>-?[0-9]+(\.[0-9]*)?)[^XYZFA]*)?",
            re.IGNORECASE)
    
    _GCODES_RE: Final = re.compile(r"G([0-9]+(?:\.[0-9]*)?)")

    _TOOL_COMMENT_REG: Final = re.compile(r"\((T[0-9])+\s")

    _COMMENT_REG: Final = re.compile(r"^(?:\s*)\((.*)\)(?:\s*)$")

    @classmethod
    def _writeLine(cls, fileHandler: TextIO, line: str, lineNumber: int) -> int:
        """
        Writes the line to the fileHandler and terminates it with a newline (\\n), adding line numbers if needed and returns the new line number
        
        :param cls: Description
        :param fileHandler: Description
        :type fileHandler: TextIO
        :param line: Description
        :type line: str
        :param lineNumber: Description
        :type lineNumber: int
        :return: Description
        :rtype: int
        """
        return cls._write(fileHandler, line + "\n", lineNumber)

    @classmethod
    def _write(cls, fileHandler: TextIO, line: str, lineNumber: int) -> int:
        """
        Writes the line to the fileHandler, adding line numbers if needed and returns the new line number
        
        :param cls: Description
        :param fileHandler: Description
        :type fileHandler: TextIO
        :param line: Description
        :type line: str
        :param lineNumber: Description
        :type lineNumber: int
        :return: Description
        :rtype: int
        """
        # Check if the line is numbered
        addLineNumbers = Settings(Settings.SEQUENCE) in (Settings.Sequences.STEP, Settings.Sequences.FILE_AND_STEP)
        digits = Settings(Settings.NAME_DIGITS) if addLineNumbers else 0
        match = cls._BODY_RE.match(line)
        if match and match.group("N") is not None: # line is numbered
            # Replace or remove the line number            
            line = re.sub(r"^N[0-9]+", f"N{str(lineNumber).rjust(digits, '0')}" if addLineNumbers else "", line, count=1)
        elif addLineNumbers: # Line is not numbered, add it
            lineNumber += Settings(Settings.NUMBERING_INTERVAL)
            line = f"N{str(lineNumber).rjust(digits, '0')} " + line
        fileHandler.write(line)
        return lineNumber
