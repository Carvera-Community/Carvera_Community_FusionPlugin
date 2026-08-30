from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LineRange:
    start: int
    stop: int | None = None

    def contains(self, line_number: int) -> bool:
        return line_number >= self.start and (
            self.stop is None or line_number < self.stop
        )


@dataclass(frozen=True)
class RapidRewrite:
    start_line: int
    end_line: int
    start_has_feed: bool


@dataclass(frozen=True)
class ParsedOperation:
    source_file: Path
    header: LineRange | None
    body: LineRange | None
    tail: LineRange | None
    tool_comment_line: int | None
    rotation_line: int | None
    shrink_line: int | None
    allow_blank_lines: bool
    rapid_rewrites: tuple[RapidRewrite, ...]

    @classmethod
    def from_context(cls, context: Any) -> "ParsedOperation":
        header_end = _optional_line(context.headerEndLine)
        body_start = _optional_line(context.bodyStartLine)
        tail_start = _optional_line(context.tailStartLine)
        rapid_rewrites = tuple(
            RapidRewrite(start, values["endLine"], values["startHasFeed"])
            for start, values in (context.rapidsAnalysis or {}).items()
        )
        return cls(
            source_file=context.tempFilePath,
            header=(LineRange(0, header_end + 1) if header_end is not None else None),
            body=(LineRange(body_start, tail_start) if body_start is not None else None),
            tail=(LineRange(tail_start) if tail_start is not None else None),
            tool_comment_line=_optional_line(context.toolCommentLine),
            rotation_line=_optional_line(context.rotationLine),
            shrink_line=_optional_line(context.shrinkLine),
            allow_blank_lines=context.allowBlankLines,
            rapid_rewrites=rapid_rewrites,
        )

    def rapid_rewrite_at(self, line_number: int) -> RapidRewrite | None:
        return next(
            (item for item in self.rapid_rewrites if item.start_line == line_number),
            None,
        )


def parsed_operation(context: Any) -> ParsedOperation:
    return context.analysis or ParsedOperation.from_context(context)


def _optional_line(value: int | None) -> int | None:
    return None if value is None or value < 0 else value
