import math
from dataclasses import dataclass
from typing import Callable

from .tokenizer import ParseResult


@dataclass
class LineResult:
    def __init__(
        self,
        line_parser: Callable[[str], ParseResult],
        index: int,
        original: str,
        previous_x: float | None,
        previous_y: float | None,
        previous_z: float | None,
    ):
        self.index = index
        self.lineNumber = index + 1
        self.original = original.rstrip("\n")
        self.parseResult = line_parser(self.original)
        self.prevX = previous_x
        self.prevY = previous_y
        self.prevZ = previous_z
        self.x: float | None = None
        self.y: float | None = None
        self.z: float | None = None
        self.effectiveMotion: str | None = None

    def setEffectiveMotion(self, motion: str | None) -> None:
        self.effectiveMotion = self.parseResult.localMotion or motion


@dataclass
class ModalState:
    motion: str | None = None
    x: float | None = 0
    y: float | None = 0
    z: float | None = 0
    feed: float | None = None


@dataclass
class XYStepDetail:
    def __init__(self, line_result: LineResult, round_decimals: int):
        self.lineNumber = line_result.lineNumber
        self.text = line_result.original
        self.x = line_result.x
        self.y = line_result.y
        self.prevX = line_result.prevX
        self.prevY = line_result.prevY
        self.prevZ = line_result.prevZ

        delta_x = (
            line_result.x - line_result.prevX
            if line_result.x is not None and line_result.prevX is not None
            else 0.0
        )
        delta_y = (
            line_result.y - line_result.prevY
            if line_result.y is not None and line_result.prevY is not None
            else 0.0
        )
        self.deltaX = round(delta_x, round_decimals)
        self.deltaY = round(delta_y, round_decimals)
        self.distance = round(math.hypot(delta_x, delta_y), round_decimals)
        self.hasZ = line_result.parseResult.sawZ


@dataclass
class ParseSegment:
    def __init__(
        self,
        start: LineResult,
        end: LineResult,
        middle_line_numbers: list[int],
        middle_texts: list[str],
        middle_steps_count: int,
        xy_steps: list[XYStepDetail],
        round_decimals: int,
    ):
        self.startLineNumber = start.lineNumber
        self.startText = start.original
        self.endLineNumber = end.lineNumber
        self.endText = end.original
        self.middleLineNumbers = middle_line_numbers
        self.middleTexts = middle_texts
        self.middleStepsCount = middle_steps_count
        self.xySteps = xy_steps

        self.totalDeltaX = round(sum(step.deltaX for step in xy_steps), round_decimals)
        self.totalDeltaY = round(sum(step.deltaY for step in xy_steps), round_decimals)
        self.totalXYDistance = round(sum(step.distance for step in xy_steps), round_decimals)

        if xy_steps:
            first = xy_steps[0]
            last = xy_steps[-1]
            net_delta_x = (last.x or 0.0) - (first.prevX or 0.0)
            net_delta_y = (last.y or 0.0) - (first.prevY or 0.0)
            self.netDeltaX = round(net_delta_x, round_decimals)
            self.netDeltaY = round(net_delta_y, round_decimals)
            self.netXYDistance = round(math.hypot(net_delta_x, net_delta_y), round_decimals)
        else:
            self.netDeltaX = None
            self.netDeltaY = None
            self.netXYDistance = None

        self.deltaZUp = (
            round(start.z - start.prevZ, round_decimals)
            if start.z is not None and start.prevZ is not None
            else 0.0
        )
        self.deltaZDown = (
            round(end.prevZ - end.z, round_decimals)
            if end.z is not None and end.prevZ is not None
            else 0.0
        )
