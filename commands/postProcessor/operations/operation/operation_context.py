from dataclasses import dataclass, field
from pathlib import Path
from re import Match
import re
from typing import Any, TextIO, TYPE_CHECKING

from ...line import Line

if TYPE_CHECKING:
    from ...processing_settings import ProcessingSettings
    from .analysis import ParsedOperation

@dataclass
class OperationContext:
    index: int
    name: str = ''
    tempFilePath: Path = field(default_factory=Path)
    lineWriter: Line = field(default_factory=Line)
    allowBlankLines: bool = False
    toolCommentLine: int = -1
    headerEndLine: int = -1
    bodyStartLine: int = -1
    tailStartLine: int = -1
    subOperationIndexWithTool: int = -1
    rotationLine: int = -1
    rotationAngle: float | None = None
    preserveRotation: bool = False
    rapidsAnalysis: dict[int, dict[str, Any]] | None = None
    shrinkLine: int = -1
    isLastOp: bool = False
    processingSettings: "ProcessingSettings | None" = None
    analysis: "ParsedOperation | None" = None


    @property
    def hasRotation(self) -> bool:
        # Parsing happens before the setup rotation angle is assigned.
        # Track whether the source operation's rotation line has already been found
        # so later A0 moves cannot replace it.
        return self.rotationLine != -1

    @property
    def hasShrink(self) -> bool:
        # check if the output contains a row that shrinks the A-axis as it can only be 
        # in the last operation otherwise it will break things.
        return self.shrinkLine != -1

    def writeLine(self, fileHandle: TextIO, line: str) -> None: self.lineWriter.writeLine(fileHandle, line)
    def write(self, fileHandle: TextIO, line: str) -> None: self.lineWriter.write(fileHandle, line)

    def matchLine(self, line: str) -> (Match[str] | None):
        return self.lineWriter._PARSE_LINE_RE.match(line)
    
    def removeFeedFromLine(self, line: str) -> str:
        return self.lineWriter.removeFeedFromLine(line)
