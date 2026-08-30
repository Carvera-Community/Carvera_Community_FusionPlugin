from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OperationSource:
    raw: Any
    name: str
    isSuppressed: bool
    hasToolpath: bool
    tool: Any | None
    toolNumber: int | None


def rawOperation(source: Any) -> Any:
    return source.raw if isinstance(source, OperationSource) else source
