from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from ..processing_settings import ProcessingSettings
from .setup.setup_context import SetupContext
from .setup.setup import Setup
from .output_path_planning import SetupOutputPathSettings, get_setup_output_path

@dataclass
class SetupsContext:
    _items: list[Setup] = field(default_factory=list)
    tempPath: Path | None = None
    fileName: str | None = None
    processingSettings: ProcessingSettings | None = None

    def capture_processing_settings(self) -> ProcessingSettings:
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
            setup.ctx.processingSettings = self.processingSettings
            setup.parse(self.tempPath)

    def rename_setups(self, find: str, replace: str, isRegex: bool, onlySelected: bool) -> None:
        setupsToRename = self.selected if onlySelected else self._items
        for setup in setupsToRename:
            setup.rename(find, replace, isRegex)
    
    def set_path(self, path: Path, sanitize_filename: Callable | None = None) -> None:
        sanitize_filename = sanitize_filename or _sanitize_filename
        current = self.processingSettings or self.capture_processing_settings()
        settings = SetupOutputPathSettings(
            flatFileStructure=current.flatFileStructure,
            numericName=current.numericName,
            operationsGrouping=current.operationsGrouping,
            fileSequence=current.fileSequence,
            fileSequenceDigits=current.fileSequenceDigits,
        )
        for setup in self.selected:
            outputPath = get_setup_output_path(
                path,
                setup,
                settings,
                sanitize_filename,
            )
            setup.set_output_path(outputPath)

    def set_file_name(self, fileName: str) -> None:
        self.fileName = fileName

        for setup in self.selected:
            setup.ctx.set_file_name(self.fileName)

    def set_file_extension(self, extension: str) -> None:
        for setup in self.selected:
            setup.set_file_extension(extension)

    @staticmethod
    def sanitize_filename(name: str) -> str:
        return _sanitize_filename(name)


def _sanitize_filename(name: str) -> str:
    from ....lib.fusionAddInUtils.general_utils import Utils

    return Utils.sanitizeFilename(name, preserveExtension=False)
