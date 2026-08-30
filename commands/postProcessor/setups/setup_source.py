from dataclasses import dataclass
from typing import Any


@dataclass
class SetupSource:
    raw: Any
    name: str
    isSelected: bool
    isSuppressed: bool
    hasError: bool
    hasWarning: bool
    machine: Any | None
    allOperations: tuple[Any, ...]


def rawSetup(source: Any) -> Any:
    return source.raw if isinstance(source, SetupSource) else source
