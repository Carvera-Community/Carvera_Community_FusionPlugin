from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ...operations.operations import Operations
    from ...processing_settings import ProcessingSettings

@dataclass
class SetupContext:
    index: int = -1
    setup: Any = None
    is_selected: bool = False
    operations: "Operations | None" = None
    processingSettings: "ProcessingSettings | None" = None

    @property
    def is_valid(self) -> bool:
        return not (self.is_suppressed or self.has_error)

    @property
    def is_suppressed(self) -> bool:
        return self.setup is not None and self.setup.isSuppressed
    
    @property
    def has_error(self) -> bool:
        return self.setup is not None and self.setup.hasError
    
    @property
    def has_warning(self) -> bool:
        return self.setup is not None and self.setup.hasWarning

    @property
    def name(self) -> str:
        if self.setup is None:
            raise ValueError("SetupContext.setup is not set.")
        return self.setup.name

    def set_file_name(self, fileName: str):
        if self.operations is not None:
            self.operations.set_file_name(fileName)
