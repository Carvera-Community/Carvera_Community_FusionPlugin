import adsk.core
from ..event_registry import EventRegistry

from ...settings.settings import Settings
from ...strings import Strings

from ...programs import Programs
from ..dialog_constants import PostDialogConstants
from .input_tab import InputTab
from .gcode_tab import GCodeTab
from .output_tab import OutputTab
from .misc_tab import MiscTab
from .tools_tab import ToolsTab

class PostDialogLayout(PostDialogConstants):
    
    @classmethod
    def createLayout(cls, command: adsk.core.Command):

        command.setDialogMinimumSize(400, 500)
        command.setDialogInitialSize(400, 500)
        command.okButtonText = Strings("Process")
        command.cancelButtonText = Strings("Close")

        # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
        inputs = command.commandInputs

        InputTab.create(inputs)
        GCodeTab.create(inputs)
        OutputTab.create(inputs)
        # cls.createToolsTab(inputs) To be added soon(tm). Hi Fae! :)
        MiscTab.create(inputs)


        InputTab._updateSetups(inputs.itemById(cls._PROGRAM_DROPDOWN_ID)) # initialize table state based on current program selection

        #region Save as default button
        separator = inputs.addSeparatorCommandInput('')

        saveButton = inputs.addBoolValueInput(cls._SAVE_ID, f"   {Strings("Save as default settings")}   ", False)
        saveButton.tooltip = Strings("TOOL TIP: Save as default settings")
        saveButton.tooltipDescription = Strings("TOOLTIP TEXT: Save as default settings")
        saveButton.isFullWidth = True
        saveButton.isEnabled = False

        EventRegistry.register(saveButton, lambda input: Settings.SaveDefault())

        def setSaveButtonEnabled(dropdown: adsk.core.DropDownCommandInput):
            dropdown.parentCommand.commandInputs.itemById(cls._SAVE_ID).isEnabled = Programs.Current is not None

        programDropdown = inputs.itemById(cls._PROGRAM_DROPDOWN_ID)
        EventRegistry.register(programDropdown, setSaveButtonEnabled)
        setSaveButtonEnabled(programDropdown) # initialize state based on current program selection

        #endregion

        # programDropdown: adsk.core.DropDownCommandInput = inputs.itemById(cls._PROGRAM_DROPDOWN_ID)
        # if programDropdown is None:
        #     return
        # selectedItem = next((listItem for listItem in programDropdown.listItems if listItem.name == Settings(Settings.NC_PROGRAM)), None)
        # if selectedItem != None and not selectedItem.isSelected:
        #     selectedItem.isSelected = True
