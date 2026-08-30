from dataclasses import dataclass
from pathlib import Path
import shutil
from typing import Callable, Protocol

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


class ProgramOutputContext(Protocol):
    def setFileName(self, fileName: str) -> None: ...


def planProgramOutput(
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


def prepareOutputFolder(outputFolder: Path, clearFolder: bool) -> bool:
    if outputFolder.exists() and not outputFolder.is_dir():
        return False

    if not clearFolder or not outputFolder.exists():
        return True

    try:
        for child in outputFolder.iterdir():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
    except OSError:
        return False

    return True


def writeProgramOutputSections(
    ctx: ProgramOutputContext,
    initialFileName: str | None,
    numericName: bool,
    writeHeader: Callable[[ProgramOutputContext], None],
    writeBody: Callable[[ProgramOutputContext], None],
    writeTail: Callable[[ProgramOutputContext], None],
) -> None:
    resetNumericName = (
        numericName
        and initialFileName is not None
        and initialFileName.isnumeric()
    )

    writeHeader(ctx)
    if resetNumericName:
        ctx.setFileName(initialFileName)

    writeBody(ctx)
    if resetNumericName:
        ctx.setFileName(initialFileName)

    writeTail(ctx)
