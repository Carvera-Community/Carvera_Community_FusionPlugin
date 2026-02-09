from ...settings.settings import Settings
from ...strings import Strings

class GCodeTab:

    @classmethod
    def createGCodeTab(cls, inputs):

        gCodeTab = inputs.addTabCommandInput(cls._GCODE_OPTIONS_GROUP_ID, Strings("G-code options"))
        gCodeTab.isEnabled = False

        #region Tool change string input
        input = gCodeTab.children.addTextBoxCommandInput(cls._TOOL_CHANGE_ID, Strings('Tool change code'), Settings(Settings.TOOL_CHANGE), 3, False)
        input.tooltip = Strings("TOOL TIP: Tool change code")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Tool change code")
        #endregion

        #region dummy input to separate the textboxes properly
        dummy = gCodeTab.children.addStringValueInput('dummy', '')
        dummy.isEnabled = False
        dummy.isReadOnly = True
        #endregion

        #region Body end codes textbox input
        input = gCodeTab.children.addTextBoxCommandInput(cls._END_CODES_ID, Strings('G-codes that mark ending sequence'), Settings(Settings.END_CODES), 3, False)
        input.tooltip = Strings("TOOL TIP: G-codes that mark ending sequence")
        input.tooltipDescription = Strings("TOOLTIP TEXT: G-codes that mark ending sequence")

        dummy = gCodeTab.children.addBoolValueInput('','', True, "", False) # As the TextBoxCommandInput above seems to be buggy we add a dummy input to create some space
        dummy.isEnabled = False
        #endregion

        #region Header end codes textbox input
        input = gCodeTab.children.addTextBoxCommandInput(cls._HEADER_CODES_ID, Strings('G-codes that mark header end'), Settings(Settings.HEADER_END_CODES), 3, False)
        input.tooltip = Strings("TOOL TIP: G-codes that mark header end")
        input.tooltipDescription = Strings("TOOLTIP TEXT: G-codes that mark header end")

        dummy = gCodeTab.children.addBoolValueInput('','', True, "", False) # As the TextBoxCommandInput above seems to be buggy we add a dummy input to create some space
        dummy.isEnabled = False
        #endregion

        #region Restore rapid moves checkbox
        input = gCodeTab.children.addBoolValueInput(cls._RESTORE_RAPID_MOVES_ID,Strings('Restore rapid moves'), True, "", Settings(Settings.RESTORE_RAPID_MOVES))
        input.tooltip = Strings("TOOL TIP: Restore rapid moves")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Restore rapid moves")
        #endregion
        #endregion -----
