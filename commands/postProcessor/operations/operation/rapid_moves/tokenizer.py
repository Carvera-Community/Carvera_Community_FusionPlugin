from dataclasses import dataclass, field
from enum import StrEnum
import re


class WORD(StrEnum):
    G = "G"
    X = "X"
    Y = "Y"
    Z = "Z"
    F = "F"


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

    def set_local_motion(self, localMotion) -> None:
        self.localMotion = localMotion


WORD_RE = re.compile(r"([A-Za-z])\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))")
COMMENT_RE = re.compile(r"\([^)]*\)")


def parse_line(line: str) -> ParseResult:
    result = ParseResult()
    clean = COMMENT_RE.sub("", line)
    raw = WORD_RE.findall(clean)
    for letter, raw_value in raw:
        letter = letter.upper()
        value = float(raw_value)
        result.words.append((letter, value))
        if letter == WORD.G:
            motion = f"{WORD.G}{int(value)}"
            if motion in MOTIONS.SUPPORTED:
                result.set_local_motion(motion)
        elif letter == WORD.X:
            result.sawX = True
        elif letter == WORD.Y:
            result.sawY = True
        elif letter == WORD.Z:
            result.sawZ = True
    return result
