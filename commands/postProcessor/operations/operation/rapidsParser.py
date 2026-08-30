from collections import deque
from pathlib import Path
from typing import Callable, Generator

from .rapid_moves.tokenizer import MOTIONS, WORD, ParseResult, parse_line
from .rapid_moves.models import LineResult, ModalState, ParseSegment, XYStepDetail
from .rapid_moves.analysis import (
    REASON_ARC_IN_MIDDLE,
    REASON_END_HAS_FEED_AND_NO_MIDDLE,
    REASON_FEED_IN_MIDDLE,
    REASON_TOO_SHORT_EFFECTIVE_DIST,
    analyze_segments,
)

class RapidsParser:
    _parseLine = staticmethod(parse_line)

    @classmethod
    def _motionOk(cls, effectiveMotion: str | None, requireG1: bool) -> bool:
        if not requireG1:
            return True
        return effectiveMotion == MOTIONS.G1

    @classmethod
    def _isZOnlyUp(cls, line: LineResult, requireG1: bool) -> bool:
        if not cls._motionOk(line.effectiveMotion, requireG1):
            return False
        if not (line.parseResult.sawZ and not (line.parseResult.sawX or line.parseResult.sawY)):
            return False
        return False if line.prevZ is None or line.z is None else line.z > line.prevZ

    @classmethod
    def _isZOnlyDown(cls, line: LineResult, requireG1: bool) -> bool:
        if not cls._motionOk(line.effectiveMotion, requireG1):
            return False
        if not (line.parseResult.sawZ and not (line.parseResult.sawX or line.parseResult.sawY)):
            return False
        return False if line.prevZ is None or line.z is None else line.z < line.prevZ

    @classmethod
    def _isXYOnly(cls, line: LineResult, requireG1: bool) -> bool:
        if not cls._motionOk(line.effectiveMotion, requireG1):
            return False
        return (line.parseResult.sawX or line.parseResult.sawY) and (not line.parseResult.sawZ)

    @classmethod
    def _isXYZAny(cls, row: LineResult, requireG1: bool) -> bool:
        if not cls._motionOk(row.effectiveMotion, requireG1):
            return False
        return row.parseResult.sawZ and (row.parseResult.sawX or row.parseResult.sawY)

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
    ) -> list[ParseSegment]:
        
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

        segments: list[ParseSegment] = []

        while True:
            window.trimTo(i)
            start = window.peek(i)
            if start is None:
                break

            if (not start.parseResult.words) or (not cls._isZOnlyUp(start, requireG1)):
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

                if cls._isZOnlyDown(line, requireG1):
                    endLineIndex = nextLineIndex
                    break

                if cls._isXYOnly(line, requireG1) or cls._isXYZAny(line, requireG1):
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

                segments.append(ParseSegment(start, end, middleLines, middleTexts, stepsTaken, xyStepDetails, roundDecimals))

                i = endLineIndex + 1
                continue

            i = start.index + 1

        return segments

    REASON_ARC_IN_MIDDLE = REASON_ARC_IN_MIDDLE
    REASON_FEED_IN_MIDDLE = REASON_FEED_IN_MIDDLE
    REASON_END_HAS_FEED_AND_NO_MIDDLE = REASON_END_HAS_FEED_AND_NO_MIDDLE
    REASON_TOO_SHORT_EFFECTIVE_DIST = REASON_TOO_SHORT_EFFECTIVE_DIST

    @classmethod
    def analyze(cls, segments: list[ParseSegment], minDist: float = 20.0):
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

        return analyze_segments(segments, minDist)
