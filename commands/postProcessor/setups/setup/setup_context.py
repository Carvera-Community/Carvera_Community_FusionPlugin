from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ...operations.operations import Operations

class SetupContext:
    index: int = -1
    setup: Any = None
    isSelected: bool = False
    operations: Optional["Operations"] = None
    rotationAngle: float | None = None
    preserveRotation: bool = False
    origin: Optional[Any] = None

    @property
    def isValid(self) -> bool:
        return not (self.isSuppressed or self.hasError)

    @property
    def isSuppressed(self) -> bool:
        return self.setup is not None and self.setup.isSuppressed
    
    @property
    def hasError(self) -> bool:
        return self.setup is not None and self.setup.hasError
    
    @property
    def hasWarning(self) -> bool:
        return self.setup is not None and self.setup.hasWarning

    @property
    def hasHeader(self) -> bool:
        return False if self.operations is None else self.operations.hasHeader

    @property
    def hasTail(self) -> bool:
        return False if self.operations is None else self.operations.hasTail

    @property
    def name(self) -> str:
        if self.setup is None:
            raise ValueError("SetupContext.setup is not set.")
        return self.setup.name

    def SetFileName(self, fileName: str):
        if self.operations is not None:
            self.operations.SetFileName(fileName)
