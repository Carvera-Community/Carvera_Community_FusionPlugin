from dataclasses import dataclass
from typing import Callable, Protocol

from ..settings.constants import Constants


class NamingContext(Protocol):
    fileName: str


class NamedOperation(Protocol):
    index: int
    name: str
    toolId: int | None

    def SetFileName(self, fileName: str) -> None: ...


@dataclass(frozen=True)
class OperationFileNamingSettings:
    operationsGrouping: Constants.OperationsGroupings
    fileSequenceDigits: int
    numericName: bool
    fileSequence: bool


def setOperationFileName(
    ctx: NamingContext,
    operation: NamedOperation,
    toolIdIndex: int,
    settings: OperationFileNamingSettings,
    sanitizeFilename: Callable[[str], str],
) -> None:
    operation.SetFileName(ctx.fileName)

    if settings.operationsGrouping in (
        Constants.OperationsGroupings.SINGLE_FILE,
        Constants.OperationsGroupings.SETUP,
    ):
        return

    fileNumber = str(operation.index + 1).rjust(settings.fileSequenceDigits, "0")

    if settings.numericName and ctx.fileName is not None:
        ctx.fileName = str(int(ctx.fileName) + 1).rjust(
            settings.fileSequenceDigits, "0"
        )
        return

    if settings.operationsGrouping == Constants.OperationsGroupings.SETUP_AND_TOOL:
        toolId = f"T{operation.toolId}"
        if toolIdIndex > 1:
            toolId += f"_{toolIdIndex}"
        if settings.fileSequence:
            toolId = f"{fileNumber}_{toolId}"
        operation.SetFileName(sanitizeFilename(f"{ctx.fileName}_{toolId}"))
    elif settings.operationsGrouping == Constants.OperationsGroupings.PER_OPERATION:
        name = f"{fileNumber}_{operation.name}" if settings.fileSequence else operation.name
        operation.SetFileName(sanitizeFilename(name))
