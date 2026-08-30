from pathlib import Path
from adsk import cam

from ....lib.fusionAddInUtils.general_utils import Utils
from ..settings.settings import Settings
from .setup.setup_context import SetupContext
from .setup.setup import Setup
from .output_path_planning import SetupOutputPathSettings, getSetupOutputPath

class SetupsContext:
    _items: list[Setup] = []
    tempPath: Path
    fileName: str | None

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
    def tools(self) -> list[cam.Tool]:
        tools = list[cam.Tool]()
        for setup in self.selected:
            tools.extend(setup.tools)
        return tools

    def load(self, setups: cam.Setups) -> None:
        # If there is no setup currently selected that is a valid setup, select all setups as default
        selectAll = not any((setup.isSelected for setup in setups if not setup.isSuppressed and not setup.hasError))
        # Intentionally loading all setups to make sure that the order is preserved
        self._items = [Setup(SetupContext(), setup, index, selectAll or setup.isSelected) for index, setup in enumerate(setups)]

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
    
    def setPath(self, path: Path) -> None:
        settings = SetupOutputPathSettings(
            flatFileStructure=bool(Settings(Settings.FLAT_FILE_STRUCTURE)),
            numericName=bool(Settings(Settings.NUMERIC_NAME)),
            operationsGrouping=Settings(Settings.OPERATIONS_GROUPING),
            fileSequence=bool(Settings(Settings.FILE_SEQUENCE)),
            fileSequenceDigits=Settings(Settings.FILE_SEQUENCE_DIGITS),
        )
        for setup in self.selected:
            outputPath = getSetupOutputPath(
                path,
                setup,
                settings,
                lambda name: Utils.sanitizeFilename(name, preserveExtension=False),
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
