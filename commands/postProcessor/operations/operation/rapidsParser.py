from pathlib import Path

from .rapid_moves.analysis import (
    REASON_ARC_IN_MIDDLE,
    REASON_END_HAS_FEED_AND_NO_MIDDLE,
    REASON_FEED_IN_MIDDLE,
    REASON_TOO_SHORT_EFFECTIVE_DIST,
    analyze_segments,
)
from .rapid_moves.models import ParseSegment
from .rapid_moves.scanner import scan_segments
from .rapid_moves.tokenizer import MOTIONS, parse_line


class RapidsParser:
    """Compatibility facade for rapid-candidate scanning and analysis."""

    _parse_line = staticmethod(parse_line)

    REASON_ARC_IN_MIDDLE = REASON_ARC_IN_MIDDLE
    REASON_FEED_IN_MIDDLE = REASON_FEED_IN_MIDDLE
    REASON_END_HAS_FEED_AND_NO_MIDDLE = REASON_END_HAS_FEED_AND_NO_MIDDLE
    REASON_TOO_SHORT_EFFECTIVE_DIST = REASON_TOO_SHORT_EFFECTIVE_DIST

    @classmethod
    def parse_file(
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
        return scan_segments(
            path,
            cls._parse_line,
            allow_blank_between=allowBlankBetween,
            require_g1=requireG1,
            round_decimals=roundDecimals,
            max_steps_between=maxStepsInbetween,
            buffer_size=bufferSize,
        )

    @classmethod
    def analyze(cls, segments: list[ParseSegment], minDist: float = 20.0):
        return analyze_segments(segments, minDist)
