import adsk.core
from ...programs import Programs
from ...settings.settings import Settings
from ...strings import Strings

from ..event_registry import EventRegistry
from ..dialog_constants import PostDialogConstants

class GCodeAnchorsTab(PostDialogConstants):

    @classmethod
    def create(cls, inputs):

        gCodeAnchorsTab = inputs.addTabCommandInput(cls._GCODE_ANCHORS_TAB_ID, Strings("G-code Anchors"))
        gCodeAnchorsTab.isEnabled = False

        def setTabEnabled(dropdown: adsk.core.DropDownCommandInput):
            dropdown.parentCommand.commandInputs.itemById(cls._GCODE_ANCHORS_TAB_ID).isEnabled = Programs.Current is not None

        programDropdown = inputs.itemById(cls._PROGRAM_DROPDOWN_ID)
        EventRegistry.register(programDropdown, setTabEnabled)
        setTabEnabled(programDropdown) # initialize state based on current program selection

        #region Tool change string input
        toolChangeCodes = gCodeAnchorsTab.children.addTextBoxCommandInput(cls._TOOL_CHANGE_ID, Strings('Tool change code'), Settings(Settings.TOOL_CHANGE), 3, False)
        toolChangeCodes.tooltip = Strings("TOOL TIP: Tool change code")
        toolChangeCodes.tooltipDescription = Strings("TOOLTIP TEXT: Tool change code")

        EventRegistry.register(toolChangeCodes, lambda input: Settings.Set(Settings.TOOL_CHANGE, input.value))

        dummy = gCodeAnchorsTab.children.addStringValueInput('', '') # As the TextBoxCommandInput above seems to be buggy we add a dummy input to create some space
        dummy.isEnabled = False
        dummy.isReadOnly = True
        #endregion

        #region Body end codes textbox input
        endCodes = gCodeAnchorsTab.children.addTextBoxCommandInput(cls._END_CODES_ID, Strings('G-codes that mark ending sequence'), Settings(Settings.END_CODES), 3, False)
        endCodes.tooltip = Strings("TOOL TIP: G-codes that mark ending sequence")
        endCodes.tooltipDescription = Strings("TOOLTIP TEXT: G-codes that mark ending sequence")

        EventRegistry.register(endCodes, lambda input: Settings.Set(Settings.END_CODES, input.value))

        dummy = gCodeAnchorsTab.children.addStringValueInput('', '') # As the TextBoxCommandInput above seems to be buggy we add a dummy input to create some space
        dummy.isEnabled = False
        dummy.isReadOnly = True
        #endregion

        #region Header end codes textbox input
        headerEndCodes = gCodeAnchorsTab.children.addTextBoxCommandInput(cls._HEADER_CODES_ID, Strings('G-codes that mark header end'), Settings(Settings.HEADER_END_CODES), 3, False)
        headerEndCodes.tooltip = Strings("TOOL TIP: G-codes that mark header end")
        headerEndCodes.tooltipDescription = Strings("TOOLTIP TEXT: G-codes that mark header end")

        EventRegistry.register(headerEndCodes, lambda input: Settings.Set(Settings.HEADER_END_CODES, input.value))

        dummy = gCodeAnchorsTab.children.addStringValueInput('', '') # As the TextBoxCommandInput above seems to be buggy we add a dummy input to create some space
        dummy.isEnabled = False
        dummy.isReadOnly = True
        #endregion

