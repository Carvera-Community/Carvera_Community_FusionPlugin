from enum import StrEnum
import math
import re
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Generator, Iterator

# G/M words (letters)
class WORD(StrEnum):
    G = "G"
    X = "X"
    Y = "Y"
    Z = "Z"
    F = "F"

# Motions (modal values)
class MOTIONS:
        G0 = "G0"
        G1 = "G1"
        G2 = "G2"
        G3 = "G3"
        SUPPORTED = (G0, G1, G2, G3)

@dataclass
class ParseResult:
    words: list[tuple[str, float]] = field(default_factory=list)
    sawX: bool = False
    sawY: bool = False
    sawZ: bool = False
    localMotion: WORD | None = None

    def setLocalMotion(self, localMotion) -> None:
        self.localMotion = localMotion

@dataclass
class LineResult:
    def __init__(self, lineParser: Callable[[str], ParseResult], index: int, original: str, prevX: float | None, prevY: float | None, prevZ: float | None):
        self._lineParser = lineParser
        self.index = index
        self.lineNumber = index + 1
        self.original = original.rstrip("\n")
        self.parseResult = self._lineParser(self.original)
        self.prevX = prevX
        self.prevY = prevY
        self.prevZ = prevZ

    x: float | None = None
    y: float | None = None
    z: float | None = None
    effectiveMotion: str | None = None

    def setEffectiveMotion(self, motion: str|None) -> None:
        self.effectiveMotion = self.parseResult.localMotion or motion

    def _motionOk(self, requireG1: bool) -> bool:
        return True if not requireG1 else self.effectiveMotion == MOTIONS.G1
    
    def isZOnlyUp(self, requireG1: bool) -> bool:
        if not self._motionOk(requireG1):
            return False
        if not (self.parseResult.sawZ and not (self.parseResult.sawX or self.parseResult.sawY)):
            return False
        return False if self.prevZ is None or self.z is None else self.z > self.prevZ

    def isZOnlyDown(self, requireG1: bool) -> bool:
        if not self._motionOk(requireG1):
            return False
        if not (self.parseResult.sawZ and not (self.parseResult.sawX or self.parseResult.sawY)):
            return False
        return False if self.prevZ is None or self.z is None else self.z < self.prevZ

    def isXYOnly(self, requireG1: bool) -> bool:
        if not self._motionOk(requireG1):
            return False
        return (self.parseResult.sawX or self.parseResult.sawY) and (not self.parseResult.sawZ)

    def isXYZAny(self, requireG1: bool) -> bool:
        if not self._motionOk(requireG1):
            return False
        return self.parseResult.sawZ and (self.parseResult.sawX or self.parseResult.sawY)


@dataclass()
class ModalState:
    motion: str | None = None
    x: float | None = 0
    y: float | None = 0
    z: float | None = 0
    feed: float | None = None

@dataclass 
class XYStepDetail:
    def __init__(self, lineResult: LineResult, roundDecimals: int):
        self.lineNumber = lineResult.lineNumber
        self.text = lineResult.original
        if lineResult.x is not None:
            self.x = lineResult.x
        if lineResult.y is not None:
            self.y = lineResult.y
        self.prevX = lineResult.prevX
        self.prevY = lineResult.prevY
        self.prevZ = lineResult.prevZ

        dX = (lineResult.x - lineResult.prevX) if (lineResult.x is not None and lineResult.prevX is not None) else 0.0
        dY = (lineResult.y - lineResult.prevY) if (lineResult.y is not None and lineResult.prevY is not None) else 0.0
        self.deltaX = round(dX, roundDecimals)
        self.deltaY = round(dY, roundDecimals)
        self.distance = round(math.hypot(dX, dY), roundDecimals)
        self.hasZ = lineResult.parseResult.sawZ

    lineNumber: int
    text: str
    x: float
    y: float
    deltaX: float
    deltaY: float
    prevX: float | None
    prevY: float | None
    prevZ: float | None
    distance: float
    hasZ: bool

@dataclass
class ParseSegment:
    def __init__(self, 
                 start: LineResult, 
                 end: LineResult, 
                 middleLineNumbers: list[int],
                 middleTexts: list[str],
                 middleStepsCount: int,
                 xySteps: list[XYStepDetail],
                 roundDecimals: int
                ):
        self.startLineNumber: int = start.lineNumber
        self.startText: str = start.original
        self.endLineNumber: int = end.lineNumber
        self.endText: str = end.original

        self.middleLineNumbers: list[int] = middleLineNumbers
        self.middleTexts: list[str] = middleTexts
        self.middleStepsCount: int = middleStepsCount
        self.xySteps: list[XYStepDetail] = xySteps

        totaldXRaw = 0.0
        totaldYRaw = 0.0
        totalXYDistRaw = 0.0
        for s in xySteps:
            totaldXRaw += s.deltaX
            totaldYRaw += s.deltaY
            totalXYDistRaw += s.distance

        self.totalDeltaX: float = round(totaldXRaw, roundDecimals)
        self.totalDeltaY: float = round(totaldYRaw, roundDecimals)
        self.totalXYDistance: float = round(totalXYDistRaw, roundDecimals)

        netdX = None
        netdY = None
        netDist = None
        if xySteps:
            first = xySteps[0]
            last = xySteps[-1]

            netdX = last.x - (first.prevX if first.prevX is not None else 0.0)
            netdY = last.y - (first.prevY if first.prevY is not None else 0.0)
            netDist = math.hypot(netdX or 0.0, netdY or 0.0)

        self.netDeltaX: float|None = None if netdX is None else round(netdX, roundDecimals)
        self.netDeltaY: float|None = None if netdY is None else round(netdY, roundDecimals)
        self.netXYDistance: float|None = None if netDist is None else round(netDist, roundDecimals)

        self.deltaZUp = round(start.z - start.prevZ, roundDecimals) if start.z is not None and start.prevZ is not None else 0.0
        self.deltaZDown = round(end.prevZ - end.z, roundDecimals) if end.z is not None and end.prevZ is not None else 0.0

class RapidsParser:
    # Regex
    WORD_RE = re.compile(r'([A-Za-z])\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))')
    COMMENT_RE = re.compile(r'\([^)]*\)')
    
    @classmethod
    def _parseLine(cls, line: str) -> ParseResult:
        result = ParseResult()
        clean = cls.COMMENT_RE.sub("", line)
        raw = cls.WORD_RE.findall(clean)
        if not raw:
            return result

        for letter, value in raw:
            letter = letter.upper()
            value = float(value)
            result.words.append((letter, value))

            if letter == WORD.G:
                g = f"{WORD.G}{int(value)}"
                if g in MOTIONS.SUPPORTED:
                    result.setLocalMotion(g)
            elif letter == WORD.X:
                result.sawX = True
            elif letter == WORD.Y:
                result.sawY = True
            elif letter == WORD.Z:
                result.sawZ = True

        return result

    @classmethod
    def _iterPerLine(cls, path: Path, lineParser: Callable[[str], ParseResult]) -> Generator[LineResult]:
        state = ModalState()

        with path.open("r", encoding="utf-8", errors="replace") as f:
            for i, original in enumerate(f):
                line = LineResult(lineParser, i, original, state.x, state.y, state.z)

                if line.parseResult.words:
                    for letter, value in line.parseResult.words:
                        if letter == WORD.G:
                            g = f"{WORD.G}{int(value)}"
                            if g in MOTIONS.SUPPORTED:
                                state.motion = g
                        elif letter == WORD.X:
                            state.x = value
                        elif letter == WORD.Y:
                            state.y = value
                        elif letter == WORD.Z:
                            state.z = value
                        elif letter == WORD.F:
                            state.feed = value

                line.x = state.x
                line.y = state.y
                line.z = state.z
                line.setEffectiveMotion(state.motion)

                yield line

    class _BufferWindow:
        """
        Holds streaming buffer state.
        """
        def __init__(self, iterator: Generator[LineResult], *, bufferSize: int):
            self.iterator: Generator[LineResult] = iterator
            self.bufferSize: int = bufferSize
            self.buffer:deque[LineResult] = deque()
            self.baseIndex: int = 0
            self.eof: bool = False

        def _fillTo(self, globalIndex: int) -> None:
            if self.eof:
                return
            while not self.eof and (self.baseIndex + len(self.buffer) - 1) < globalIndex:
                try:
                    self.buffer.append(next(self.iterator))
                except StopIteration:
                    self.eof = True
                    break

        def peek(self, globalIndex: int) -> LineResult | None:
            if globalIndex < self.baseIndex:
                return None
            self._fillTo(globalIndex)
            offset = globalIndex - self.baseIndex
            if 0 <= offset < len(self.buffer):
                return self.buffer[offset]
            return None

        def trimTo(self, globalIndex: int) -> None:
            # Drop everything strictly before globalIndex
            while self.buffer and self.baseIndex < globalIndex:
                self.buffer.popleft()
                self.baseIndex += 1

            # Keep memory bounded
            while len(self.buffer) > self.bufferSize:
                self.buffer.popleft()
                self.baseIndex += 1

    @classmethod
    def parseFile(
        cls,
        path: Path,
        *,
        allowBlankBetween: bool = True,
        requireG1: bool = True,
        roundDecimals: int = 6,
        maxStepsInbetween: int = 3,
        bufferSize: int = 20,
    ) -> Iterator[ParseSegment]:
        
        if maxStepsInbetween < 0:
            raise ValueError("maxStepsInbetween must be >= 0")

        bufferSize = max(bufferSize, maxStepsInbetween + 8)

        it = cls._iterPerLine(path, cls._parseLine)
        window = cls._BufferWindow(it, bufferSize=bufferSize)

        def _nextNonEmpty(currentLineIndex: int) -> int | None:
            nextNonBlankLine = currentLineIndex + 1
            while True:
                row = window.peek(nextNonBlankLine)
                if row is None:
                    return None
                if row.parseResult.words:
                    return nextNonBlankLine
                if not allowBlankBetween:
                    return None
                nextNonBlankLine += 1

        i = 0

        while True:
            window.trimTo(i)
            start = window.peek(i)
            if start is None:
                break

            if (not start.parseResult.words) or (not start.isZOnlyUp(requireG1)):
                i += 1
                continue

            xyStepDetails: list[XYStepDetail] = []
            middleLineIndexes: list[int] = []

            nextLineIndex = _nextNonEmpty(start.index)
            if nextLineIndex is None:
                break

            stepsTaken = 0
            endLineIndex: int | None = None
            aborted = False
            sawAnyXY = False

            while nextLineIndex is not None:
                line = window.peek(nextLineIndex)
                if line is None:
                    aborted = True
                    break

                if line.isZOnlyDown(requireG1):
                    endLineIndex = nextLineIndex
                    break

                if line.isXYOnly(requireG1) or line.isXYZAny(requireG1):
                    middleLineIndexes.append(nextLineIndex)
                    stepsTaken += 1

                    if line.parseResult.sawX or line.parseResult.sawY:
                        sawAnyXY = True

                        xyStepDetails.append(XYStepDetail(line, roundDecimals))

                    if stepsTaken > maxStepsInbetween:
                        aborted = True
                        break

                    nextLineIndex = _nextNonEmpty(line.index)
                    continue

                aborted = True
                break

            if (not aborted) and (endLineIndex is not None) and sawAnyXY:
                end = window.peek(endLineIndex)
                if end is None:
                    break

                middleLines = []
                middleTexts = []
                for k in middleLineIndexes:
                    result = window.peek(k)
                    if result is None:
                        aborted = True
                        break
                    middleLines.append(result.lineNumber)
                    middleTexts.append(result.original)
                if aborted:
                    i += 1
                    continue

                yield ParseSegment(start, end, middleLines, middleTexts, stepsTaken, xyStepDetails, roundDecimals)

                i = endLineIndex + 1
                continue

            i = start.index + 1

    REASON_ARC_IN_MIDDLE = "arc_in_middle"
    REASON_FEED_IN_MIDDLE = "feed_in_middle"
    REASON_END_HAS_FEED_AND_NO_MIDDLE = "end_has_feed_and_no_middle"
    REASON_TOO_SHORT_EFFECTIVE_DIST = "too_short_effectiveDist"

    @classmethod
    def analyze(cls, segments: Iterator[ParseSegment], minDist: float = 20.0) -> Generator[dict[str, Any]]:
        """
        Generates a list of dictionaries containing the start and end line of all 
        the candidates for rapid moves and a flag if it is deemed a valid rapid movement.

        Rules for rejections:
        - Reject if any middle-step line contains G2/G3 (arc) or F (feed).
        - Reject if ending line contains feed, move back one line until it is valid or run out of middle lines.
        - Reject if effectiveDist < minDist, where:
                zDist = abs(dZUp) + abs(dZDown)
                effectiveDist = max(totalXYDist, zDist)
        """

        def _tokenize(line: str) -> list[str]:
            tokens = []
            for t in [t.strip().upper() for t in line.replace("\t", " ").split() if t.strip()]:
                if t.startswith(WORD.G) and len(t) > 1 and t[1:].isdigit():
                    # Normalize G-codes: G02 → G2, G03 → G3, G00 → G0, etc.
                    number = int(t[1:])
                    tokens.append(f"G{number}")
                else:
                    tokens.append(t)
            return tokens
        
        def _hasArc(tokens: list[str]) -> bool:
            for token in tokens:
                if token == MOTIONS.G2 or token == MOTIONS.G3:
                    return True
            return False

        def _hasFeed(tokens: list[str]) -> bool:
            # Feed usually appears as "F333.3". We look for tokens starting with 'F' and having digits after it.
            for token in tokens:
                if len(token) >= 2 and token[0] == WORD.F:
                    if any(ch.isdigit() for ch in token[1:]):
                        return True
            return False

        for segment in segments:
            result = AnalysisSegment(segment)

            # Check if the first line has a feed
            # Start is eligible even if it is G1 + F (Fusion transition)
            # But if start has a feed token, mark it so writeBody can strip feed when injecting G0
            tokens = _tokenize(segment.startText)
            result.hasStartHasFeed = _hasFeed(tokens)

            # Rule: If ending line contains feed, move back one line until it is valid or run out of middle lines.
            result.trimEndUntilValidOrNoMiddle(_tokenize, _hasFeed, cls.REASON_END_HAS_FEED_AND_NO_MIDDLE)

            # Rule: disqualify if middle steps contain arc/feed tokens
            for line in segment.middleTexts:
                tokens = _tokenize(line)
                if _hasArc(tokens):
                    result.isValid = False
                    result.addRejectReason(cls.REASON_ARC_IN_MIDDLE)
                
                if _hasFeed(tokens):
                    result.isValid = False
                    result.addRejectReason(cls.REASON_FEED_IN_MIDDLE)

            # Rule: calculate effective distance and disqualify if too short
            if result.getEffectiveLength() < float(minDist):
                result.isValid = False
                result.addRejectReason(cls.REASON_TOO_SHORT_EFFECTIVE_DIST)

            yield result.asDict()
    
@dataclass
class AnalysisSegment:
    def __init__(self, lineResult: ParseSegment) -> None:
        self.lineResult = lineResult
        self.startLineNumber = lineResult.startLineNumber
        self.startText = lineResult.startText
        self.endLineNumber = lineResult.endLineNumber
        self.endText = lineResult.endText
        self.middleTexts = lineResult.middleTexts
        self.middleLineNumbers = lineResult.middleLineNumbers
        self.deltaZUp = lineResult.deltaZUp
        self.deltaZDown = lineResult.deltaZDown
        self.totalXYDistance = lineResult.totalXYDistance
        self.isValid: bool = True
        self.hasStartHasFeed: bool = False

        self._rejectReason: list[str] = []


    @property
    def middleStepsCount(self) -> int:
        return len(self.middleTexts)

    def addRejectReason(self, rejectReason: str) -> None:
        self._rejectReason.append(rejectReason)

    def trimEndUntilValidOrNoMiddle(self, tokenizer: Callable[[str], list[str]], validator: Callable[[list[str]], bool], rejectionReason: str) -> None: 
        tokens = tokenizer(self.endText)
        #if validator(tokens):
        while validator(tokens) and len(self.middleTexts) > 0:
            self.endText = self.middleTexts[-1]
            self.endLineNumber = self.middleLineNumbers[-1]
            self.middleTexts.pop()
            self.middleLineNumbers.pop()
            tokens = tokenizer(self.endText)

        if validator(tokens) and self.middleStepsCount == 0:
            self.isValid = False
            self.addRejectReason(rejectionReason)

    def getEffectiveLength(self) -> float:
        zDist = abs(self.deltaZUp) + abs(self.deltaZDown)
        return zDist + zDist

    def asDict(self) -> dict[str, Any]:
        d: dict[str, Any] = {}

        d['startLine'] = self.startLineNumber
        d['endLine'] = self.endLineNumber
        d['startHasFeed'] = self.hasStartHasFeed
        d['isValid'] = self.isValid

        return d