from dataclasses import dataclass
from typing import Any, Callable, Generator

from .models import ParseSegment
from .tokenizer import MOTIONS, WORD


REASON_ARC_IN_MIDDLE = "arc_in_middle"
REASON_FEED_IN_MIDDLE = "feed_in_middle"
REASON_END_HAS_FEED_AND_NO_MIDDLE = "end_has_feed_and_no_middle"
REASON_TOO_SHORT_EFFECTIVE_DIST = "too_short_effectiveDist"


@dataclass
class AnalysisSegment:
    def __init__(self, parsed_segment: Any) -> None:
        self.lineResult = parsed_segment
        self.startLineNumber = parsed_segment.startLineNumber
        self.startText = parsed_segment.startText
        self.endLineNumber = parsed_segment.endLineNumber
        self.endText = parsed_segment.endText
        self.middleTexts = parsed_segment.middleTexts
        self.middleLineNumbers = parsed_segment.middleLineNumbers
        self.deltaZUp = parsed_segment.deltaZUp
        self.deltaZDown = parsed_segment.deltaZDown
        self.totalXYDistance = parsed_segment.totalXYDistance
        self.isValid = True
        self.hasStartHasFeed = False
        self._rejectReason: list[str] = []

    @property
    def middle_steps_count(self) -> int:
        return len(self.middleTexts)

    def add_reject_reason(self, rejectReason: str) -> None:
        self._rejectReason.append(rejectReason)

    def trim_end_until_valid_or_no_middle(
        self,
        tokenizer: Callable[[str], list[str]],
        validator: Callable[[list[str]], bool],
        rejectionReason: str,
    ) -> None:
        tokens = tokenizer(self.endText)
        if validator(tokens):
            while validator(tokens) and self.middleTexts:
                self.endText = self.middleTexts[-1]
                self.endLineNumber = self.middleLineNumbers[-1]
                self.middleTexts.pop()
                self.middleLineNumbers.pop()
                tokens = tokenizer(self.endText)

            if validator(tokens) and self.middle_steps_count == 0:
                self.isValid = False
                self.add_reject_reason(rejectionReason)

    def get_effective_length(self) -> float:
        z_distance = abs(self.deltaZUp) + abs(self.deltaZDown)
        return max(self.totalXYDistance, z_distance)

    def as_dict(self) -> dict[str, Any]:
        return {
            "startLine": self.startLineNumber,
            "endLine": self.endLineNumber,
            "startHasFeed": self.hasStartHasFeed,
            "isValid": self.isValid,
        }


def tokenize_analysis_line(line: str) -> list[str]:
    tokens = []
    for token in (
        token.strip().upper()
        for token in line.replace("\t", " ").split()
        if token.strip()
    ):
        if token.startswith(WORD.G) and len(token) > 1 and token[1:].isdigit():
            tokens.append(f"G{int(token[1:])}")
        else:
            tokens.append(token)
    return tokens


def has_arc(tokens: list[str]) -> bool:
    return MOTIONS.G2 in tokens or MOTIONS.G3 in tokens


def has_feed(tokens: list[str]) -> bool:
    return any(
        len(token) >= 2
        and token[0] == WORD.F
        and any(character.isdigit() for character in token[1:])
        for token in tokens
    )


def analyze_segments(
    segments: list[ParseSegment],
    min_distance: float = 20.0,
) -> Generator[dict[str, Any]]:
    for segment in segments:
        result = AnalysisSegment(segment)
        result.hasStartHasFeed = has_feed(tokenize_analysis_line(segment.startText))
        result.trim_end_until_valid_or_no_middle(
            tokenize_analysis_line,
            has_feed,
            REASON_END_HAS_FEED_AND_NO_MIDDLE,
        )

        for line in segment.middleTexts:
            tokens = tokenize_analysis_line(line)
            if has_arc(tokens):
                result.isValid = False
                result.add_reject_reason(REASON_ARC_IN_MIDDLE)
            if has_feed(tokens):
                result.isValid = False
                result.add_reject_reason(REASON_FEED_IN_MIDDLE)

        if result.get_effective_length() < float(min_distance):
            result.isValid = False
            result.add_reject_reason(REASON_TOO_SHORT_EFFECTIVE_DIST)

        yield result.as_dict()
