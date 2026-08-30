from pathlib import Path
from typing import Callable, Protocol

from ..file_modes import FileModes


class BodyOperationContext(Protocol):
    rotationAngle: float | None
    preserveRotation: bool


class BodyOperation(Protocol):
    hasBody: bool
    toolId: int | None
    fileName: str
    ctx: BodyOperationContext

    def WriteBody(self, fileHandle) -> None: ...


class BodyContext(Protocol):
    operations: list[BodyOperation]
    path: Path
    fileExtension: str
    rotationAngle: float | None
    preserveRotation: bool


def _currentFileNameSetter():
    from .operations import setOperationFileName

    return setOperationFileName


def writeBody(ctx: BodyContext, setFileName: Callable | None = None):
    setFileName = setFileName or _currentFileNameSetter()

    toolIdIndex = {}
    firstOperation: bool = True
    for operation in [op for op in ctx.operations if op.hasBody]:
        if firstOperation:
            operation.ctx.rotationAngle = ctx.rotationAngle
            operation.ctx.preserveRotation = ctx.preserveRotation
        else:
            operation.ctx.preserveRotation = False

        toolId = operation.toolId
        if toolId not in toolIdIndex:
            toolIdIndex[toolId] = 0
        toolIdIndex[toolId] += 1

        setFileName(ctx, operation, toolIdIndex[toolId])

        pathToOpen: Path = ctx.path / f"{operation.fileName}{ctx.fileExtension}"
        with pathToOpen.open(FileModes.APPEND) as fileHandle:
            operation.WriteBody(fileHandle)

        if firstOperation:
            firstOperation = False
