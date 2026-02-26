import math
import re
from collections import deque
from dataclasses import dataclass
from pathlib import Path


class RapidsParser:
    # Regex
    WORD_RE = re.compile(r'([A-Za-z])\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))')
    COMMENT_RE = re.compile(r'\([^)]*\)')

    # G/M words (letters)
    class WORD:
        G = "G"
        X = "X"
        Y = "Y"
        Z = "Z"
        F = "F"
    
    # Motions (modal values)
    class MOTION:
            G0 = "G0"
            G1 = "G1"
            G2 = "G2"
            G3 = "G3"
            SUPPORTED = (G0, G1, G2, G3)

    # perLine dict keys
    K_IDX = "idx"
    K_LINENO = "lineno"
    K_ORIGINAL = "original"
    K_WORDS = "words"
    K_SAW_X = "sawX"
    K_SAW_Y = "sawY"
    K_SAW_Z = "sawZ"
    K_PREV_X = "prevX"
    K_PREV_Y = "prevY"
    K_PREV_Z = "prevZ"
    K_X = "x"
    K_Y = "y"
    K_Z = "z"
    K_EFFECTIVE_MOTION = "effectiveMotion"

    # Segment output keys
    O_SEGMENTS = "segments"
    O_START_LINE = "startLine"
    O_START = "start"
    O_END_LINE = "endLine"
    O_END = "end"
    O_MIDDLE_LINES = "middleLines"
    O_MIDDLE = "middle"
    O_MIDDLE_STEPS_COUNT = "middleStepsCount"
    O_DZ_UP = "dZUp"
    O_DZ_DOWN = "dZDown"
    O_XY_STEPS = "xySteps"
    O_TOTAL_DX = "totaldX"
    O_TOTAL_DY = "totaldY"
    O_TOTAL_XY_DIST = "totalXYDist"
    O_NET_DX = "netdX"
    O_NET_DY = "netdY"
    O_NET_XY_DIST = "netXYDist"

    # XY step detail keys
    S_LINE = "line"
    S_TEXT = "text"
    S_DX = "dX"
    S_DY = "dY"
    S_DIST = "dist"
    S_HAS_Z = "hasZ"
    S_PREV_X = "prevX"
    S_PREV_Y = "prevY"
    S_X = "x"
    S_Y = "y"

    @dataclass
    class ModalState:
        motion: str | None = None
        x: float | None = None
        y: float | None = None
        z: float | None = None
        feed: float | None = None

    @classmethod
    def _parseLine(cls, line: str):
        clean = cls.COMMENT_RE.sub("", line)
        raw = cls.WORD_RE.findall(clean)
        if not raw:
            return [], False, False, False, None

        words: list[tuple[str, float]] = []
        sawX = sawY = sawZ = False
        localMotion = None

        for letter, value in raw:
            letter = letter.upper()
            value = float(value)
            words.append((letter, value))

            if letter == cls.WORD.G:
                g = f"{cls.WORD.G}{int(value)}"
                if g in cls.MOTION.SUPPORTED:
                    localMotion = g
            elif letter == cls.WORD.X:
                sawX = True
            elif letter == cls.WORD.Y:
                sawY = True
            elif letter == cls.WORD.Z:
                sawZ = True

        return words, sawX, sawY, sawZ, localMotion

    @classmethod
    def _motionOk(cls, effectiveMotion: str | None, requireG1: bool) -> bool:
        if not requireG1:
            return True
        return effectiveMotion == cls.MOTION.G1

    @classmethod
    def _isZOnlyUp(cls, row, requireG1: bool) -> bool:
        if not cls._motionOk(row[cls.K_EFFECTIVE_MOTION], requireG1):
            return False
        if not (row[cls.K_SAW_Z] and not (row[cls.K_SAW_X] or row[cls.K_SAW_Y])):
            return False
        if row[cls.K_PREV_Z] is None or row[cls.K_Z] is None:
            return False
        return row[cls.K_Z] > row[cls.K_PREV_Z]

    @classmethod
    def _isZOnlyDown(cls, row, requireG1: bool) -> bool:
        if not cls._motionOk(row[cls.K_EFFECTIVE_MOTION], requireG1):
            return False
        if not (row[cls.K_SAW_Z] and not (row[cls.K_SAW_X] or row[cls.K_SAW_Y])):
            return False
        if row[cls.K_PREV_Z] is None or row[cls.K_Z] is None:
            return False
        return row[cls.K_Z] < row[cls.K_PREV_Z]

    @classmethod
    def _isXYOnly(cls, row, requireG1: bool) -> bool:
        if not cls._motionOk(row[cls.K_EFFECTIVE_MOTION], requireG1):
            return False
        return (row[cls.K_SAW_X] or row[cls.K_SAW_Y]) and (not row[cls.K_SAW_Z])

    @classmethod
    def _isXYZAny(cls, row, requireG1: bool) -> bool:
        if not cls._motionOk(row[cls.K_EFFECTIVE_MOTION], requireG1):
            return False
        return row[cls.K_SAW_Z] and (row[cls.K_SAW_X] or row[cls.K_SAW_Y])

    @classmethod
    def _iterPerLine(cls, path: Path):
        state = cls.ModalState()

        with path.open("r", encoding="utf-8", errors="replace") as f:
            for i, original in enumerate(f):
                words, sawX, sawY, sawZ, localMotion = cls._parseLine(original)

                prev_x = state.x
                prev_y = state.y
                prev_z = state.z

                if words:
                    for letter, value in words:
                        if letter == cls.WORD.G:
                            g = f"{cls.WORD.G}{int(value)}"
                            if g in cls.MOTION.SUPPORTED:
                                state.motion = g
                        elif letter == cls.WORD.X:
                            state.x = value
                        elif letter == cls.WORD.Y:
                            state.y = value
                        elif letter == cls.WORD.Z:
                            state.z = value
                        elif letter == cls.WORD.F:
                            state.feed = value

                effectiveMotion = (localMotion or state.motion)

                yield {
                    cls.K_IDX: i,
                    cls.K_LINENO: i + 1,
                    cls.K_ORIGINAL: original.rstrip("\n"),
                    cls.K_WORDS: words,
                    cls.K_SAW_X: sawX,
                    cls.K_SAW_Y: sawY,
                    cls.K_SAW_Z: sawZ,
                    cls.K_PREV_X: prev_x,
                    cls.K_PREV_Y: prev_y,
                    cls.K_PREV_Z: prev_z,
                    cls.K_X: state.x,
                    cls.K_Y: state.y,
                    cls.K_Z: state.z,
                    cls.K_EFFECTIVE_MOTION: effectiveMotion,
                }

    class _BufferWindow:
        """
        Holds streaming buffer state.
        """
        def __init__(self, iterator, *, bufferSize: int):
            self.iterator = iterator
            self.bufferSize = bufferSize
            self.buffer = deque()
            self.baseIndex = 0
            self.eof = False

        def _fillTo(self, globalIndex: int) -> None:
            if self.eof:
                return
            while not self.eof and (self.baseIndex + len(self.buffer) - 1) < globalIndex:
                try:
                    self.buffer.append(next(self.iterator))
                except StopIteration:
                    self.eof = True
                    break

        def peek(self, globalIndex: int):
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
    ):
        if maxStepsInbetween < 0:
            raise ValueError("maxStepsInbetween must be >= 0")

        bufferSize = max(bufferSize, maxStepsInbetween + 8)

        it = cls._iterPerLine(path)
        window = cls._BufferWindow(it, bufferSize=bufferSize)

        def _nextNonEmpty(currentLineIndex: int) -> int | None:
            nextNonBlankLine = currentLineIndex + 1
            while True:
                row = window.peek(nextNonBlankLine)
                if row is None:
                    return None
                if row[cls.K_WORDS]:
                    return nextNonBlankLine
                if not allowBlankBetween:
                    return None
                nextNonBlankLine += 1

        segments = []
        i = 0

        while True:
            window.trimTo(i)
            start = window.peek(i)
            if start is None:
                break

            if (not start[cls.K_WORDS]) or (not cls._isZOnlyUp(start, requireG1)):
                i += 1
                continue

            middleLineIndexes: list[int] = []
            XYStepDetails = []

            nextLineIndex = _nextNonEmpty(start[cls.K_IDX])
            if nextLineIndex is None:
                break

            stepsTaken = 0
            endLineIndex: int | None = None
            aborted = False
            sawAnyXY = False

            while nextLineIndex is not None:
                row = window.peek(nextLineIndex)
                if row is None:
                    aborted = True
                    break

                if cls._isZOnlyDown(row, requireG1):
                    endLineIndex = nextLineIndex
                    break

                if cls._isXYOnly(row, requireG1) or cls._isXYZAny(row, requireG1):
                    middleLineIndexes.append(nextLineIndex)
                    stepsTaken += 1

                    if row[cls.K_SAW_X] or row[cls.K_SAW_Y]:
                        sawAnyXY = True

                        dx_raw = (row[cls.K_X] - row[cls.K_PREV_X]) if (row[cls.K_X] is not None and row[cls.K_PREV_X] is not None) else 0.0
                        dy_raw = (row[cls.K_Y] - row[cls.K_PREV_Y]) if (row[cls.K_Y] is not None and row[cls.K_PREV_Y] is not None) else 0.0
                        dist_raw = math.hypot(dx_raw, dy_raw)

                        XYStepDetails.append(
                            {
                                cls.S_LINE: row[cls.K_LINENO],
                                cls.S_TEXT: row[cls.K_ORIGINAL],
                                cls.S_DX: round(dx_raw, roundDecimals),
                                cls.S_DY: round(dy_raw, roundDecimals),
                                cls.S_DIST: round(dist_raw, roundDecimals),
                                cls.S_HAS_Z: bool(row[cls.K_SAW_Z]),
                                cls.S_PREV_X: row[cls.K_PREV_X],
                                cls.S_PREV_Y: row[cls.K_PREV_Y],
                                cls.S_X: row[cls.K_X],
                                cls.S_Y: row[cls.K_Y],
                            }
                        )

                    if stepsTaken > maxStepsInbetween:
                        aborted = True
                        break

                    nextLineIndex = _nextNonEmpty(row[cls.K_IDX])
                    continue

                aborted = True
                break

            if (not aborted) and (endLineIndex is not None) and sawAnyXY:
                end = window.peek(endLineIndex)
                if end is None:
                    break

                dZUp = round(start[cls.K_Z] - start[cls.K_PREV_Z], roundDecimals)
                dZDown = round(end[cls.K_PREV_Z] - end[cls.K_Z], roundDecimals)

                totaldXRaw = 0.0
                totaldYRaw = 0.0
                totalXYDistRaw = 0.0
                for s in XYStepDetails:
                    dxr = (s[cls.S_X] - s[cls.S_PREV_X]) if (s[cls.S_X] is not None and s[cls.S_PREV_X] is not None) else 0.0
                    dyr = (s[cls.S_Y] - s[cls.S_PREV_Y]) if (s[cls.S_Y] is not None and s[cls.S_PREV_Y] is not None) else 0.0
                    totaldXRaw += dxr
                    totaldYRaw += dyr
                    totalXYDistRaw += math.hypot(dxr, dyr)

                netdX = None
                netdY = None
                netDist = None
                if XYStepDetails:
                    first = XYStepDetails[0]
                    last = XYStepDetails[-1]

                    if first[cls.S_PREV_X] is not None and last[cls.S_X] is not None:
                        netdX = last[cls.S_X] - first[cls.S_PREV_X]
                    if first[cls.S_PREV_Y] is not None and last[cls.S_Y] is not None:
                        netdY = last[cls.S_Y] - first[cls.S_PREV_Y]
                    if (netdX is not None) or (netdY is not None):
                        netDist = math.hypot(netdX or 0.0, netdY or 0.0)

                    for s in XYStepDetails:
                        s.pop(cls.S_PREV_X, None)
                        s.pop(cls.S_PREV_Y, None)
                        s.pop(cls.S_X, None)
                        s.pop(cls.S_Y, None)

                middleLines = []
                middleTexts = []
                for k in middleLineIndexes:
                    r = window.peek(k)
                    if r is None:
                        aborted = True
                        break
                    middleLines.append(r[cls.K_LINENO])
                    middleTexts.append(r[cls.K_ORIGINAL])
                if aborted:
                    i += 1
                    continue

                segments.append(
                    {
                        cls.O_START_LINE: start[cls.K_LINENO],
                        cls.O_START: start[cls.K_ORIGINAL],
                        cls.O_END_LINE: end[cls.K_LINENO],
                        cls.O_END: end[cls.K_ORIGINAL],
                        cls.O_MIDDLE_LINES: middleLines,
                        cls.O_MIDDLE: middleTexts,
                        cls.O_MIDDLE_STEPS_COUNT: stepsTaken,
                        cls.O_DZ_UP: dZUp,
                        cls.O_DZ_DOWN: dZDown,
                        cls.O_XY_STEPS: XYStepDetails,
                        cls.O_TOTAL_DX: round(totaldXRaw, roundDecimals),
                        cls.O_TOTAL_DY: round(totaldYRaw, roundDecimals),
                        cls.O_TOTAL_XY_DIST: round(totalXYDistRaw, roundDecimals),
                        cls.O_NET_DX: None if netdX is None else round(netdX, roundDecimals),
                        cls.O_NET_DY: None if netdY is None else round(netdY, roundDecimals),
                        cls.O_NET_XY_DIST: None if netDist is None else round(netDist, roundDecimals),
                    }
                )

                i = endLineIndex + 1
                continue

            i = start[cls.K_IDX] + 1

        return segments


    KEY_IS_VALID = "isValid"
    KEY_REASONS = "reasons"
    KEY_DZ_UP = "dZUp"
    KEY_DZ_DOWN = "dZDown"
    KEY_TOTAL_XY_DIST = "totalXYDist"
    KEY_MIDDLE = "middle"
    KEY_Z_DIST = "zDist"
    KEY_EFFECTIVE_DIST = "effectiveDist"
    KEY_START_HAS_FEED = "startHasFeed"
    REASON_ARC_IN_MIDDLE = "arc_in_middle"
    REASON_FEED_IN_MIDDLE = "feed_in_middle"
    REASON_END_HAS_FEED_AND_NO_MIDDLE = "end_has_feed_and_no_middle"
    REASON_TOO_SHORT_EFFECTIVE_DIST = "too_short_effectiveDist"

    @classmethod
    def analyze(cls, segments, minDist: float = 20.0):
        """
        Mutates the segment list (from parseFile) by setting:
        - isValid: bool
        - reasons: list[str]
        - zDist: float
        - effectiveDist: float

        Rules:
        - Reject if any middle-step line contains G2/G3 (arc) or F (feed).
        - Reject if ending line contains feed, move back one line until it is valid or run out of middle lines.
        - Reject if effectiveDist < minDist, where:
                zDist = abs(dZUp) + abs(dZDown)
                effectiveDist = max(totalXYDist, zDist)
        """

        def _tokenize(line: str):
            tokens = []
            for t in [t.strip().upper() for t in line.replace("\t", " ").split() if t.strip()]:
                if t.startswith(cls.WORD.G) and len(t) > 1 and t[1:].isdigit():
                    # Normalize G-codes: G02 → G2, G03 → G3, G00 → G0, etc.
                    number = int(t[1:])
                    tokens.append(f"G{number}")
                else:
                    tokens.append(t)
            return tokens
        
        def _hasArc(tokens):
            for token in tokens:
                if token == cls.MOTION.G2 or token == cls.MOTION.G3:
                    return True
            return False

        def _hasFeed(tokens):
            # Feed usually appears as "F333.3". We look for tokens starting with 'F' and having digits after it.
            for token in tokens:
                if len(token) >= 2 and token[0] == cls.WORD.F:
                    if any(ch.isdigit() for ch in token[1:]):
                        return True
            return False

        for segment in segments:
            segment[cls.KEY_IS_VALID] = True
            segment[cls.KEY_REASONS] = []

            # Check if the first line has a feed
            # Start is eligible even if it is G1 + F (Fusion transition)
            # But if startHasFeed, mark it so writeBody can strip feed when injecting G0
            tokens = _tokenize(segment[cls.O_START])
            segment[cls.KEY_START_HAS_FEED] = _hasFeed(tokens)

            # Rule: disqualify if middle steps contain arc/feed tokens
            for line in (segment.get(cls.KEY_MIDDLE, []) or []):
                tokens = _tokenize(line)

                if _hasArc(tokens):
                    segment[cls.KEY_IS_VALID] = False
                    segment[cls.KEY_REASONS].append(cls.REASON_ARC_IN_MIDDLE)

                if _hasFeed(tokens):
                    segment[cls.KEY_IS_VALID] = False
                    segment[cls.KEY_REASONS].append(cls.REASON_FEED_IN_MIDDLE)

            # Rule: If ending line contains feed, move back one line until it is valid or run out of middle lines.
            tokens = _tokenize(segment[cls.O_END])
            if _hasFeed(tokens):
                middle = segment.get(cls.O_MIDDLE, [])
                middleLines = segment.get(cls.O_MIDDLE_LINES, [])
                while _hasFeed(tokens) and len(middleLines) > 0:
                    segment[cls.O_END] = middle[-1]
                    segment[cls.O_END_LINE] = middleLines[-1]
                    middle.pop()
                    middleLines.pop()
                    tokens = _tokenize(segment[cls.O_END])
                
                segment[cls.O_MIDDLE] = middle
                segment[cls.O_MIDDLE_LINES] = middleLines
                segment[cls.O_MIDDLE_STEPS_COUNT] = len(segment[cls.O_MIDDLE_LINES])

                if _hasFeed(tokens) and (len(segment.get(cls.O_MIDDLE_LINES, [])) == 0):
                    segment[cls.KEY_IS_VALID] = False
                    segment[cls.KEY_REASONS].append(cls.REASON_END_HAS_FEED_AND_NO_MIDDLE)

            # Rule: calculate effective distance and disqualify if too short
            dZUp = float(segment.get(cls.KEY_DZ_UP, 0.0) or 0.0)
            dZDown = float(segment.get(cls.KEY_DZ_DOWN, 0.0) or 0.0)
            totalXYDist = float(segment.get(cls.KEY_TOTAL_XY_DIST, 0.0) or 0.0)

            zDist = abs(dZUp) + abs(dZDown)
            effectiveDist = totalXYDist + zDist

            segment[cls.KEY_Z_DIST] = zDist
            segment[cls.KEY_EFFECTIVE_DIST] = effectiveDist

            if effectiveDist < float(minDist):
                segment[cls.KEY_IS_VALID] = False
                segment[cls.KEY_REASONS].append(cls.REASON_TOO_SHORT_EFFECTIVE_DIST)

        return segments