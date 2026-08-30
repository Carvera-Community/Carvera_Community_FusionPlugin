from dataclasses import dataclass
from typing import Any, Callable


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
    def middleStepsCount(self) -> int:
        return len(self.middleTexts)

    def addRejectReason(self, rejectReason: str) -> None:
        self._rejectReason.append(rejectReason)

    def trimEndUntilValidOrNoMiddle(
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

            if validator(tokens) and self.middleStepsCount == 0:
                self.isValid = False
                self.addRejectReason(rejectionReason)

    def getEffectiveLength(self) -> float:
        z_distance = abs(self.deltaZUp) + abs(self.deltaZDown)
        return max(self.totalXYDistance, z_distance)

    def asDict(self) -> dict[str, Any]:
        return {
            "startLine": self.startLineNumber,
            "endLine": self.endLineNumber,
            "startHasFeed": self.hasStartHasFeed,
            "isValid": self.isValid,
        }
