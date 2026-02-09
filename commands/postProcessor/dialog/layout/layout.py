import adsk

from ...settings.settings import Settings
from ...strings import Strings

from .input_tab import InputTab
from .gcode_tab import GCodeTab
from .output_tab import OutputTab
from .misc_tab import MiscTab
from .tools_tab import ToolsTab

class PostDialogLayout(InputTab, GCodeTab, OutputTab, MiscTab, ToolsTab):
    
    @classmethod
    def createLayout(cls, command: adsk.core.Command):

        command.setDialogMinimumSize(465, 580)
        command.setDialogInitialSize(465, 580)
        command.okButtonText = Strings("Process")
        command.cancelButtonText = Strings("Close")

        # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
        inputs = command.commandInputs

        cls.createInputTab(inputs)
        cls.createGCodeTab(inputs)
        cls.createOutputTab(inputs)
        cls.createMiscTab(inputs)
        cls.createToolsTab(inputs)

        #region Save as default button
        input = inputs.addSeparatorCommandInput('dummy')

        input = inputs.addBoolValueInput(cls._SAVE_ID, f"   {Strings("Save as default settings")}   ", False)
        input.tooltip = Strings("TOOL TIP: Save as default settings")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Save as default settings")
        input.isFullWidth = True
        input.isEnabled = False
        #endregion

        programDropdown: adsk.core.DropDownCommandInput = inputs.itemById(cls._PROGRAM_DROPDOWN_ID)
        selectedItem = next((listItem for listItem in programDropdown.listItems if listItem.name == Settings(Settings.NC_PROGRAM)), None)
        if selectedItem != None and not selectedItem.isSelected:
            selectedItem.isSelected = True
