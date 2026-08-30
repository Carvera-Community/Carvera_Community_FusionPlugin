from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TYPE_CHECKING

from .operation.operation import Operation

if TYPE_CHECKING:
    from ..processing_settings import ProcessingSettings

@dataclass
class OperationsContext:
    operations: list[Operation] = field(default_factory=list)
    path: Path = field(default_factory=Path)
    fileName: str = ''
    fileExtension: str = ''
    rotationAngle: float | None = None
    preserveRotation: bool = False
    operationWithHeader: Operation | None = None
    operationWithTail: Operation | None = None
    fileNameTarget: Any = None
    processingSettings: "ProcessingSettings | None" = None
