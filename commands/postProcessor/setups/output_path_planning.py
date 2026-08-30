from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from ..settings.constants import Constants


class NamedSetup(Protocol):
    index: int
    name: str


@dataclass(frozen=True)
class SetupOutputPathSettings:
    flatFileStructure: bool
    numericName: bool
    operationsGrouping: Constants.OperationsGroupings
    fileSequence: bool
    fileSequenceDigits: int


def get_setup_output_path(
    basePath: Path,
    setup: NamedSetup,
    settings: SetupOutputPathSettings,
    sanitizeFilename: Callable[[str], str],
) -> Path:
    sharedPath = (
        settings.flatFileStructure
        or settings.numericName
        or settings.operationsGrouping
        in (
            Constants.OperationsGroupings.SINGLE_FILE,
            Constants.OperationsGroupings.SETUP,
        )
    )
    if sharedPath:
        return basePath

    prefix = ""
    if settings.fileSequence:
        prefix = str(setup.index + 1).rjust(settings.fileSequenceDigits, "0") + "_"
    return basePath / f"{prefix}{sanitizeFilename(setup.name)}"
