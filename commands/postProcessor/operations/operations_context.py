from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from .operation.operation import Operation

if TYPE_CHECKING:
    from ..processing_settings import ProcessingSettings

@dataclass
class OperationsContext:
    operations: list[Operation] = field(default_factory=list)
    path: Path = field(default_factory=Path)
    file_name: str = ''
    file_extension: str = ''
    operation_with_tail: Operation | None = None
    processingSettings: "ProcessingSettings | None" = None
