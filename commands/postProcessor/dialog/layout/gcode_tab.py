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

        dummy = gCodeTab.children.addStringValueInput('', '') # As the TextBoxCommandInput above seems to be buggy we add a dummy input to create some space
        dummy.isEnabled = False
        dummy.isReadOnly = True
        #endregion

        #region Body end codes textbox input
        input = gCodeTab.children.addTextBoxCommandInput(cls._END_CODES_ID, Strings('G-codes that mark ending sequence'), Settings(Settings.END_CODES), 3, False)
        input.tooltip = Strings("TOOL TIP: G-codes that mark ending sequence")
        input.tooltipDescription = Strings("TOOLTIP TEXT: G-codes that mark ending sequence")

        dummy = gCodeTab.children.addStringValueInput('', '') # As the TextBoxCommandInput above seems to be buggy we add a dummy input to create some space
        dummy.isEnabled = False
        dummy.isReadOnly = True
        #endregion

        #region Header end codes textbox input
        input = gCodeTab.children.addTextBoxCommandInput(cls._HEADER_CODES_ID, Strings('G-codes that mark header end'), Settings(Settings.HEADER_END_CODES), 3, False)
        input.tooltip = Strings("TOOL TIP: G-codes that mark header end")
        input.tooltipDescription = Strings("TOOLTIP TEXT: G-codes that mark header end")

        dummy = gCodeTab.children.addStringValueInput('', '') # As the TextBoxCommandInput above seems to be buggy we add a dummy input to create some space
        dummy.isEnabled = False
        dummy.isReadOnly = True
        #endregion

        #region Combine tool checkbox
        input = gCodeTab.children.addBoolValueInput(cls._COMBINE_TOOLS_ID, Strings('Combine operations using same tool'), True, "", Settings(Settings.COMBINE_TOOL))
        input.tooltip = Strings("TOOL TIP: Combine operations using same tool")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Combine operations using same tool")
        #endregion

        #region Rotate A-Axis between setups checkbox
        input = gCodeTab.children.addBoolValueInput(cls._ROTATE_A_AXIS_ID, Strings('Rotate A-Axis between setups'), True, "", Settings(Settings.ROTATE_A_AXIS))
        input.tooltip = Strings("TOOL TIP: Rotate A-Axis between setups")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Rotate A-Axis between setups")
        #endregion

        #region Retract to safe Y on A-axis rotation checkbox
        input = gCodeTab.children.addBoolValueInput(cls._SAFE_Y_RETRACTION_ID, Strings("Retract Y on A-axis rotation"), True, "", Settings(Settings.SAFE_Y_RETRACTION))
        input.tooltip = Strings("TOOL TIP: Retract Y on A-axis rotation")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Retract Y on A-axis rotation")
        #endregion

        #region Safe Y-retraction coordinate number
        input = gCodeTab.children.addIntegerSpinnerCommandInput(cls._Y_RETRACTION_COORDINATE_ID, Strings("Safe Y-retraction coordinate (mm)"), -150, 0, 1, Settings(Settings.Y_RETRACTION_COORDINATE))
        input.tooltip = Strings("TOOL TIP: Safe Y-retraction coordinate (mm)")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Safe Y-retraction coordinate (mm)")
        #endregion

        #region Restore rapid moves checkbox
        input = gCodeTab.children.addBoolValueInput(cls._RESTORE_RAPID_MOVES_ID,Strings('Restore rapid moves'), True, "", Settings(Settings.RESTORE_RAPID_MOVES))
        input.tooltip = Strings("TOOL TIP: Restore rapid moves")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Restore rapid moves")
        #endregion
        #endregion -----
