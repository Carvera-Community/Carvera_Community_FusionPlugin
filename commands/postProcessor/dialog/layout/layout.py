from adsk.core import (
    Command,
    CommandInput
)
from ...setups.setups_context import SetupsContext

from ..event_registry import EventRegistry

from ...settings.settings import Settings
from ...strings import Strings

from ...programs import Programs
from ..constants import Constants
from .input_tab import InputTab
from .gcode_tab import GCodeTab
from .output_tab import OutputTab
from .misc_tab import MiscTab
from .tools_tab import ToolsTab

class PostDialogLayout(Constants):
    
    @classmethod
    def createLayout(cls, command: Command, ctx: SetupsContext):

        command.setDialogMinimumSize(400, 500)
        command.setDialogInitialSize(400, 500)
        command.okButtonText = Strings("Process")
        command.cancelButtonText = Strings("Close")

        # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
        inputs = command.commandInputs

        InputTab.create(inputs, ctx)
        GCodeTab.create(inputs)
        OutputTab.create(inputs)
        ToolsTab.create(ctx, inputs)
        MiscTab.create(inputs, ctx)

        InputTab._updateSetups(inputs.itemById(cls.PROGRAM_DROPDOWN_ID), ctx) # initialize table state based on current program selection

        #region Save as default button
        #separator = inputs.addSeparatorCommandInput('')

        saveButton = inputs.addBoolValueInput(cls.SAVE_ID, "   " + Strings("Save as default settings") + "   ", False)
        saveButton.tooltip = Strings("TOOLTIP: Save as default settings")
        saveButton.tooltipDescription = Strings("TOOLTIP TEXT: Save as default settings")
        saveButton.isFullWidth = True
        saveButton.isEnabled = False

        EventRegistry.register(cls.SAVE_ID, lambda input: Settings.SaveDefault())

        def setSaveButtonEnabled(input: CommandInput):
            input.parentCommand.commandInputs.itemById(cls.SAVE_ID).isEnabled = Programs.Current is not None

        EventRegistry.register(cls.PROGRAM_DROPDOWN_ID, setSaveButtonEnabled)
        setSaveButtonEnabled(inputs.itemById(cls.PROGRAM_DROPDOWN_ID)) # initialize state based on current program selection

        #endregion
