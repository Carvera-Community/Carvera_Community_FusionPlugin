from dataclasses import dataclass
from pathlib import Path
import shutil

from .settings.constants import Constants


@dataclass(frozen=True)
class ProgramOutputSettings:
    operationsGrouping: Constants.OperationsGroupings
    flatFileStructure: bool
    numericName: bool
    clearFolder: bool


@dataclass(frozen=True)
class ProgramOutputLayout:
    path: Path
    fileName: str


def plan_program_output(
    outputFolder: Path,
    fileName: str | None,
    settings: ProgramOutputSettings,
) -> ProgramOutputLayout:
    numericFileName = (
        settings.numericName
        and fileName is not None
        and fileName.isnumeric()
    )
    usesBaseFolder = (
        settings.operationsGrouping == Constants.OperationsGroupings.SINGLE_FILE
        or settings.flatFileStructure
        or numericFileName
    )
    return ProgramOutputLayout(
        path=outputFolder if usesBaseFolder else outputFolder / str(fileName),
        fileName=str(fileName),
    )


def prepare_output_folder(outputFolder: Path, clearFolder: bool) -> None:
    if outputFolder.exists() and not outputFolder.is_dir():
        raise NotADirectoryError(f"Output path is not a directory: {outputFolder}")

    if not clearFolder or not outputFolder.exists():
        return

    for child in outputFolder.iterdir():
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()
