from dataclasses import dataclass
from typing import Callable, Protocol

from ..settings.constants import Constants


class NamedOperation(Protocol):
    index: int
    name: str
    tool_id: int | None



@dataclass(frozen=True)
class OperationFileNamingSettings:
    operationsGrouping: Constants.OperationsGroupings
    fileSequenceDigits: int
    numericName: bool
    fileSequence: bool


def get_operation_file_name(
    base_file_name: str,
    operation: NamedOperation,
    tool_id_index: int,
    settings: OperationFileNamingSettings,
    sanitize_filename: Callable[[str], str],
) -> tuple[str, str]:
    file_name = base_file_name

    if settings.operationsGrouping in (
        Constants.OperationsGroupings.SINGLE_FILE,
        Constants.OperationsGroupings.SETUP,
    ):
        return file_name, base_file_name

    if settings.numericName:
        next_base_name = str(int(base_file_name) + 1).rjust(
            settings.fileSequenceDigits, "0"
        )
        return file_name, next_base_name

    file_number = str(operation.index + 1).rjust(settings.fileSequenceDigits, "0")

    if settings.operationsGrouping == Constants.OperationsGroupings.SETUP_AND_TOOL:
        toolId = f"T{operation.tool_id}"
        if tool_id_index > 1:
            toolId += f"_{tool_id_index}"
        if settings.fileSequence:
            toolId = f"{file_number}_{toolId}"
        file_name = sanitize_filename(f"{base_file_name}_{toolId}")
    elif settings.operationsGrouping == Constants.OperationsGroupings.PER_OPERATION:
        name = f"{file_number}_{operation.name}" if settings.fileSequence else operation.name
        file_name = sanitize_filename(name)

    return file_name, base_file_name
