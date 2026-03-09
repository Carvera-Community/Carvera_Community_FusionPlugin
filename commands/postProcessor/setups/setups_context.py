from pathlib import Path
from typing import Iterator
from adsk.cam import (
    Setups as adskSetups,
    Tool
)

from ....lib.fusionAddInUtils.general_utils import Utils
from ..settings.settings import Settings
from .setup.setup_context import SetupContext
from .setup.setup import Setup

class SetupsContext:
    _items: list[Setup] = []
    tempPath: Path
    fileName: str | None

    @property
    def valid(self) -> Iterator[Setup]:
        for setup in self._items:
            if setup.ctx.isValid:
                yield setup

    @property
    def selected(self) -> Iterator[Setup]: 
        for setup in self.valid:
            if setup.isSelected:
                yield setup

    @property
    def hasSelected(self) -> bool:
        return any(self.selected)

    def load(self, setups: adskSetups) -> None:
        # If there is no setup currently selected that is a valid setup, select all setups as default
        selectAll = not any((setup.isSelected for setup in setups if not setup.isSuppressed and not setup.hasError))
        # Intentionally loading all setups to make sure that the order is preserved
        self._items = [Setup(SetupContext(), setup, index, selectAll or setup.isSelected) for index, setup in enumerate(setups)]

    def parse(self, tempPath: Path) -> None:
        self.tempPath = tempPath
        for setup in self.selected:
            setup.Parse(self.tempPath)
#        return

    def renameSetups(self, find: str, replace: str, isRegex: bool, onlySelected: bool) -> None:
        setupsToRename = self.selected if onlySelected else self._items
        for setup in setupsToRename:
            setup.Rename(find, replace, isRegex)
    
    def setPath(self, path: Path) -> None:
        outputPath: Path = path
        for setup in self.selected:
            if (not (Settings(Settings.FLAT_FILE_STRUCTURE) 
                    or Settings(Settings.NUMERIC_NAME) 
                    or Settings(Settings.OPERATIONS_GROUPING) in [Settings.OperationsGroupings.SINGLE_FILE, 
                                                                    Settings.OperationsGroupings.SETUP])):
                fileNumber = str(setup.index + 1).rjust(Settings(Settings.FILE_SEQUENCE_DIGITS), "0") + '_' if Settings(Settings.FILE_SEQUENCE) else ""
                outputPath = path / f"{fileNumber}{Utils.sanitizeFilename(setup.name, preserveExtension = False)}"
            setup.SetOutputPath(outputPath)

    def setFileName(self, fileName: str) -> None:
        # This check should not be needed
        # if (Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SINGLE_FILE 
        #     or Settings(Settings.NUMERIC_NAME)):
        self.fileName = fileName

        setup: Setup
        for setup in self.selected:
                setup.ctx.SetFileName(self.fileName)

    def setFileExtension(self, extension: str) -> None:
        for setup in self.selected:
            setup.SetFileExtension(extension)

    def getTools(self) -> Iterator[Tool]:
        for setup in self.selected:
            for tool in setup.ctx.getTools():
                yield tool