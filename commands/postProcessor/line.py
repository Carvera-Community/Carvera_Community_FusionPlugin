
import re
from typing import Final, TextIO

class Line():

    _BODY_RE: Final = re.compile(r""
        r"(?P<N>N[0-9]+ *)?" # line number
        r"(?P<line>"         # line w/o number
        r"(M(?P<M>[0-9]+) *)?" # M-code
        r"(G(?P<G>[0-9]+(?:\.[0-9]*)?) *)?" # G-code
        r"(T(?P<T>[0-9]+))?" # Tool
        r".+)",              # to end of line
        re.IGNORECASE | re.DOTALL)

    _PARSE_LINE_RE: Final = re.compile(r""
            r"(G(?P<G>[0-9]+(\.[0-9]*)?)[^XYZFAR]*)?"
            r"(?P<XY>((X-?[0-9]+(\.[0-9]*)?)[^XYZFAR]*)?((Y-?[0-9]+(\.[0-9]*)?)[^XYZFAR]*)?)"
            r"(A(?P<A>-?[0-9]+(\.[0-9]*)?)[^XYZFAR]*)?"
            r"(R(?P<R>-?[0-9]+(\.[0-9]*)?)[^XYZFAR]*)?"
            r"(Z(?P<Z>-?[0-9]+(\.[0-9]*)?)[^XYZFAR]*)?"
            r"(F(?P<F>-?[0-9]+(\.[0-9]*)?)[^XYZFAR]*)?",
            re.IGNORECASE)
    
    _GCODES_RE: Final = re.compile(r"G([0-9]+(?:\.[0-9]*)?)")

    _TOOL_COMMENT_REG: Final = re.compile(r"\(T[0-9]+\s.*\)$")

    _COMMENT_REG: Final = re.compile(r"^(?:\s*)\((.*)\)(?:\s*)$")

    _RE_FEED = re.compile(r'(^|\s)F[+-]?\d+(?:\.\d*)?(?=\s|$)', re.IGNORECASE)

    @classmethod
    def writeLine(cls, fileHandler: TextIO, line: str) -> None:
        """Write one line, removing an input line number when present."""
        return cls.write(fileHandler, line + "\n")

    @classmethod
    def write(cls, fileHandler: TextIO, line: str) -> None:
        """Write text after removing an input line number when present."""
        # Check if the line is numbered
        match = cls._BODY_RE.match(line)
        if match and match.group("N") is not None: # line is numbered
            # Remove the line number            
            line = re.sub(r"^N[0-9]+", "", line, count=1)
        fileHandler.write(line)

    @classmethod
    def removeFeedFromLine(cls, line: str) -> str:
        return cls._RE_FEED.sub(r'\1', line).strip()
