from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from ..processing_settings import ProcessingSettings
from .setup.setup_context import SetupContext
from .setup.setup import Setup
from .output_path_planning import SetupOutputPathSettings, getSetupOutputPath

@dataclass
class SetupsContext:
    _items: list[Setup] = field(default_factory=list)
    tempPath: Path | None = None
    fileName: str | None = None
    processingSettings: ProcessingSettings | None = None

    def captureProcessingSettings(self) -> ProcessingSettings:
        self.processingSettings = ProcessingSettings.capture()
        return self.processingSettings

    @property
    def valid(self) -> list[Setup]:
        return [setup for setup in self._items if setup.ctx.isValid]

    @property
    def selected(self) -> list[Setup]: 
        return [setup for setup in self.valid if setup.isSelected]

    @property
    def hasSelected(self) -> bool:
        return any(self.selected)

    @property
    def tools(self) -> list[Any]:
        tools = []
        for setup in self.selected:
            tools.extend(setup.tools)
        return tools

    def load(self, setups, setupFactory: Callable = Setup) -> None:
        # If there is no setup currently selected that is a valid setup, select all setups as default
        selectAll = not any((setup.isSelected for setup in setups if not setup.isSuppressed and not setup.hasError))
        # Intentionally loading all setups to make sure that the order is preserved
        self._items = [setupFactory(SetupContext(), setup, index, selectAll or setup.isSelected) for index, setup in enumerate(setups)]

    def parse(self, tempPath: Path) -> None:
        if not self.selected:
            return
        self.tempPath = tempPath
        for setup in self.selected:
            setup.Parse(self.tempPath)
#        return

    def renameSetups(self, find: str, replace: str, isRegex: bool, onlySelected: bool) -> None:
        setupsToRename = self.selected if onlySelected else self._items
        for setup in setupsToRename:
            setup.Rename(find, replace, isRegex)
    
    def setPath(self, path: Path, sanitizeFilename: Callable | None = None) -> None:
        sanitizeFilename = sanitizeFilename or _sanitizeFilename
        current = self.processingSettings or self.captureProcessingSettings()
        settings = SetupOutputPathSettings(
            flatFileStructure=current.flatFileStructure,
            numericName=current.numericName,
            operationsGrouping=current.operationsGrouping,
            fileSequence=current.fileSequence,
            fileSequenceDigits=current.fileSequenceDigits,
        )
        for setup in self.selected:
            outputPath = getSetupOutputPath(
                path,
                setup,
                settings,
                sanitizeFilename,
            )
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


def _sanitizeFilename(name: str) -> str:
    from ....lib.fusionAddInUtils.general_utils import Utils

    return Utils.sanitizeFilename(name, preserveExtension=False)
