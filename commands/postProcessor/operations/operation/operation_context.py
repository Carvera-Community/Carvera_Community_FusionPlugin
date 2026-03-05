from dataclasses import dataclass
from pathlib import Path
from re import Match
import re
from typing import Any, TextIO

from ...line import Line

@dataclass
class OperationContext:
    def __init__(self, index: int) -> None:
        self.index = index

    index: int
    name: str = ''
    tempFilePath: Path = Path()
    lineWriter: Line = Line()
    allowBlankLines: bool = False
    toolCommentLine: int = -1
    headerEndLine: int = -1
    bodyStartLine: int = -1
    tailStartLine: int = -1
    subOperationIndexWithTool: int = -1
    hasRotation: bool = False
    rotationLine: int = -1
    rotationAngle: float | None = None
    preserveRotation: bool | None = False
    rapidsAnalysis: dict[int, dict[str, Any]] | None = None


    def writeLine(self, fileHandle: TextIO, line: str) -> None: self.lineWriter.writeLine(fileHandle, line)
    def write(self, fileHandle: TextIO, line: str) -> None: self.lineWriter.write(fileHandle, line)

    def matchLine(self, line: str) -> (Match[str] | None):
        return self.lineWriter._PARSE_LINE_RE.match(line)
    
    def removeFeedFromLine(self, line: str) -> str:
        return self.lineWriter.removeFeedFromLine(line)