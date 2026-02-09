import adsk
from ...settings.settings import Settings
from ...strings import Strings

class MiscTab:
    @classmethod
    def createMiscTab(cls, inputs: adsk.core.CommandInputs):

        miscTab = inputs.addTabCommandInput(cls._RENAME_SETUPS_GROUP_ID, Strings("Misc"))

        #region ----- [ Rename setups group ] -----
        group = miscTab.children.addGroupCommandInput(cls._RENAME_SETUPS_GROUP_ID, Strings("Rename Setups"))
        group.isExpanded = True

        #region Use regex checkbox
        input = group.children.addBoolValueInput(cls._USE_REGEX_ID, Strings("Use Python regular expressions"), True, "", Settings(Settings.USE_REGEX))
        input.tooltip = Strings("TOOL TIP: Use Python regular expressions")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Use Python regular expressions")
        #endregion

        #region Find string input
        input = group.children.addStringValueInput(cls._FIND_STRING_ID, Strings("Search for this string"), Settings(Settings.FIND_STRING))
        input.tooltip = Strings("TOOL TIP: Search for this string")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Search for this string")
        #endregion

        #region Replace string input
        input = group.children.addStringValueInput(cls._REPLACE_STRING_ID, Strings("Replace with this string"), Settings(Settings.REPLACE_STRING))
        input.tooltip = Strings("TOOL TIP: Replace with this string")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Replace with this string")
        #endregion

        #region Replace button
        input = group.children.addBoolValueInput(cls._REPLACE_ID, f"   {Strings("Search and replace")}   ", False)
        input.isFullWidth = True
        input.tooltip = Strings("TOOL TIP: Search and replace")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Search and replace")
        #endregion
        #endregion -----

        #region ----- [ Advanced settings ] -----
        group = miscTab.children.addGroupCommandInput(cls._ADVANCED_SETTINGS_GROUP_ID, Strings("Advanced Settings"))
        group.isExpanded = True

        #region Initial delay spinner input
        input = group.children.addFloatSpinnerCommandInput(cls._INITIAL_DELAY_ID, Strings("Initial time allowance"), "s", 0.1, 1.0, 0.1, Settings(Settings.INITIAL_DELAY))
        input.tooltip = Strings("TOOL TIP: Initial time allowance")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Initial time allowance")
        #endregion

        #region Post retries spinner input
        input = group.children.addIntegerSpinnerCommandInput(cls._POST_RETRIES_ID, Strings("Number of retries"), 1, 9, 1, Settings(Settings.POST_RETRIES))
        input.tooltip = Strings("TOOL TIP: Number of retries")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Number of retries")
        #endregion
        #endregion -----
