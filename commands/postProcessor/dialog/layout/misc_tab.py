import adsk.core
from ...settings.settings import Settings
from ...strings import Strings
from ...programs import Programs

from ..event_registry import EventRegistry
from ..dialog_constants import PostDialogConstants

class MiscTab(PostDialogConstants):
    @classmethod
    def create(cls, inputs: adsk.core.CommandInputs):

        miscTab = inputs.addTabCommandInput(cls._RENAME_SETUPS_GROUP_ID, Strings("Misc"))

        def setTabEnabled(dropdown: adsk.core.DropDownCommandInput):
            dropdown.parentCommand.commandInputs.itemById(cls._OUTPUT_GROUP_ID).isEnabled = Programs.Current is not None

        programDropdown = inputs.itemById(cls._PROGRAM_DROPDOWN_ID)
        EventRegistry.register(programDropdown, setTabEnabled)
        setTabEnabled(programDropdown) # initialize state based on current program selection

        group = miscTab.children.addGroupCommandInput(cls._RENAME_SETUPS_GROUP_ID, Strings("Rename Setups"))
        group.isExpanded = True

        #region Use regex checkbox
        useRegex = group.children.addBoolValueInput(cls._USE_REGEX_ID, Strings("Use Python regular expressions"), True, "", Settings(Settings.USE_REGEX))
        useRegex.tooltip = Strings("TOOL TIP: Use Python regular expressions")
        useRegex.tooltipDescription = Strings("TOOLTIP TEXT: Use Python regular expressions")

        EventRegistry.register(useRegex, lambda input: Settings.Set(Settings.USE_REGEX, input.value))
        #endregion

        #region Find string input
        findText = group.children.addStringValueInput(cls._FIND_STRING_ID, Strings("Search for this string"), Settings(Settings.FIND_STRING))
        findText.tooltip = Strings("TOOL TIP: Search for this string")
        findText.tooltipDescription = Strings("TOOLTIP TEXT: Search for this string")
        EventRegistry.register(findText, lambda input: Settings.Set(Settings.FIND_STRING, input.value))
        #endregion

        #region Replace string input
        replaceText = group.children.addStringValueInput(cls._REPLACE_STRING_ID, Strings("Replace with this string"), Settings(Settings.REPLACE_STRING))
        replaceText.tooltip = Strings("TOOL TIP: Replace with this string")
        replaceText.tooltipDescription = Strings("TOOLTIP TEXT: Replace with this string")
        EventRegistry.register(replaceText, lambda input: Settings.Set(Settings.REPLACE_STRING, input.value))
        #endregion

        #region Replace button
        replaceButton = group.children.addBoolValueInput(cls._REPLACE_ID, f"   {Strings("Search and replace")}   ", False)
        replaceButton.isFullWidth = True
        replaceButton.tooltip = Strings("TOOL TIP: Search and replace")
        replaceButton.tooltipDescription = Strings("TOOLTIP TEXT: Search and replace")
        #endregion
