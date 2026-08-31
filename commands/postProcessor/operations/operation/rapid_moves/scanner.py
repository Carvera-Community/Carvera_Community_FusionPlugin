from collections import deque
from pathlib import Path
from typing import Callable, Generator, Iterator

from .models import LineResult, ModalState, ParseSegment, XYStepDetail
from .tokenizer import MOTIONS, WORD, ParseResult


def iter_modal_lines(path: Path, line_parser: Callable[[str], ParseResult]) -> Generator[LineResult]:
    state = ModalState()
    with path.open("r", encoding="utf-8", errors="replace") as source:
        for index, original in enumerate(source):
            line = LineResult(line_parser, index, original, state.x, state.y, state.z)
            for letter, value in line.parseResult.words:
                if letter == WORD.G:
                    motion = f"{WORD.G}{int(value)}"
                    if motion in MOTIONS.SUPPORTED:
                        state.motion = motion
                elif letter == WORD.X:
                    state.x = value
                elif letter == WORD.Y:
                    state.y = value
                elif letter == WORD.Z:
                    state.z = value
                elif letter == WORD.F:
                    state.feed = value
            line.x, line.y, line.z = state.x, state.y, state.z
            line.set_effective_motion(state.motion)
            yield line


class BufferWindow:
    """Bounded random-lookahead window over a streaming line iterator."""

    def __init__(self, iterator: Iterator[LineResult], *, buffer_size: int):
        self.iterator = iterator
        self.buffer_size = buffer_size
        self.buffer: deque[LineResult] = deque()
        self.base_index = 0
        self.eof = False

    def _fill_to(self, global_index: int) -> None:
        while not self.eof and self.base_index + len(self.buffer) - 1 < global_index:
            try:
                self.buffer.append(next(self.iterator))
            except StopIteration:
                self.eof = True

    def peek(self, global_index: int) -> LineResult | None:
        if global_index < self.base_index:
            return None
        self._fill_to(global_index)
        offset = global_index - self.base_index
        return self.buffer[offset] if 0 <= offset < len(self.buffer) else None

    def trim_to(self, global_index: int) -> None:
        while self.buffer and self.base_index < global_index:
            self.buffer.popleft()
            self.base_index += 1
        while len(self.buffer) > self.buffer_size:
            self.buffer.popleft()
            self.base_index += 1


def scan_segments(
    path: Path,
    line_parser: Callable[[str], ParseResult],
    *,
    allow_blank_between: bool = True,
    require_g1: bool = True,
    round_decimals: int = 6,
    max_steps_between: int = 3,
    buffer_size: int = 20,
) -> list[ParseSegment]:
    if max_steps_between < 0:
        raise ValueError("max_steps_between must be >= 0")

    window = BufferWindow(
        iter_modal_lines(path, line_parser),
        buffer_size=max(buffer_size, max_steps_between + 8),
    )

    def next_non_empty(current_index: int) -> int | None:
        candidate_index = current_index + 1
        while True:
            row = window.peek(candidate_index)
            if row is None:
                return None
            if row.parseResult.words:
                return candidate_index
            if not allow_blank_between:
                return None
            candidate_index += 1

    segments: list[ParseSegment] = []
    index = 0
    while True:
        window.trim_to(index)
        start = window.peek(index)
        if start is None:
            return segments
        if not start.parseResult.words or not _is_z_only(start, require_g1, up=True):
            index += 1
            continue

        middle_indexes: list[int] = []
        xy_steps: list[XYStepDetail] = []
        next_index = next_non_empty(start.index)
        end_index = None
        aborted = next_index is None

        while next_index is not None:
            line = window.peek(next_index)
            if line is None:
                aborted = True
                break
            if _is_z_only(line, require_g1, up=False):
                end_index = next_index
                break
            if not (_is_xy_only(line, require_g1) or _is_xyz(line, require_g1)):
                aborted = True
                break
            middle_indexes.append(next_index)
            if line.parseResult.sawX or line.parseResult.sawY:
                xy_steps.append(XYStepDetail(line, round_decimals))
            if len(middle_indexes) > max_steps_between:
                aborted = True
                break
            next_index = next_non_empty(line.index)

        if not aborted and end_index is not None and xy_steps:
            end = window.peek(end_index)
            middle = [window.peek(item) for item in middle_indexes]
            if end is not None and all(item is not None for item in middle):
                rows = [item for item in middle if item is not None]
                segments.append(ParseSegment(
                    start, end,
                    [item.lineNumber for item in rows],
                    [item.original for item in rows],
                    len(middle_indexes), xy_steps, round_decimals,
                ))
                index = end_index + 1
                continue
        index = start.index + 1


def _motion_matches(line: LineResult, require_g1: bool) -> bool:
    return not require_g1 or line.effectiveMotion == MOTIONS.G1


def _is_z_only(line: LineResult, require_g1: bool, *, up: bool) -> bool:
    parsed = line.parseResult
    if not _motion_matches(line, require_g1) or not parsed.sawZ or parsed.sawX or parsed.sawY:
        return False
    if line.prevZ is None or line.z is None:
        return False
    return line.z > line.prevZ if up else line.z < line.prevZ


def _is_xy_only(line: LineResult, require_g1: bool) -> bool:
    parsed = line.parseResult
    return _motion_matches(line, require_g1) and (parsed.sawX or parsed.sawY) and not parsed.sawZ


def _is_xyz(line: LineResult, require_g1: bool) -> bool:
    parsed = line.parseResult
    return _motion_matches(line, require_g1) and parsed.sawZ and (parsed.sawX or parsed.sawY)
