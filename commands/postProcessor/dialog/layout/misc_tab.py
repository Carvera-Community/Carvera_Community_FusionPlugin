import adsk.core
from ...settings.settings import Settings
from ...strings import Strings
from ...programs import Programs
from ...setups.setups import Setups

from ..event_registry import EventRegistry
from ..dialog_constants import PostDialogConstants

from .input_tab import InputTab

class MiscTab(PostDialogConstants):
    @classmethod
    def create(cls, inputs: adsk.core.CommandInputs):

        miscTab = inputs.addTabCommandInput(cls._RENAME_SETUPS_GROUP_ID, Strings("Misc"))

        def setTabEnabled(dropdown: adsk.core.DropDownCommandInput):
            dropdown.parentCommand.commandInputs.itemById(cls._OUTPUT_GROUP_ID).isEnabled = Programs.Current is not None

        programDropdown = inputs.itemById(cls._PROGRAM_DROPDOWN_ID)
        EventRegistry.register(programDropdown, setTabEnabled)
        setTabEnabled(programDropdown) # initialize state based on current program selection

        #region Language dropdown
        languageDropdown = miscTab.children.addDropDownCommandInput(cls._LANGUAGE_ID, Strings("Language"), adsk.core.DropDownStyles.TextListDropDownStyle)
        languageDropdown.tooltip = Strings("TOOLTIP: Language")
        languageDropdown.tooltipDescription = (Strings("TOOLTIP TEXT: Language {fileVersion}")).format(fileVersion = Strings.fileVersion)

        languageTexts = Strings.GetAvailableLanguages()

        for language in languageTexts:
            languageDropdown.listItems.add(languageTexts[language], language == Settings(Settings.LANGUAGE))

        EventRegistry.register(languageDropdown, lambda dropdown: Settings(Settings.LANGUAGE, Strings.GetLanguageSetting(dropdown.selectedItem.name)))
        #endregion


        group = miscTab.children.addGroupCommandInput(cls._RENAME_SETUPS_GROUP_ID, Strings("Rename Setups"))
        group.isExpanded = True

        #region Use regex checkbox
        useRegex = group.children.addBoolValueInput(cls._USE_REGEX_ID, Strings("Use Python regular expressions"), True, "", Settings(Settings.USE_REGEX))
        useRegex.tooltip = Strings("TOOLTIP: Use Python regular expressions")
        useRegex.tooltipDescription = Strings("TOOLTIP TEXT: Use Python regular expressions")

        EventRegistry.register(useRegex, lambda input: Settings.Set(Settings.USE_REGEX, input.value))
        #endregion

        #region Find string input
        findText = group.children.addStringValueInput(cls._FIND_STRING_ID, Strings("Search for this string"), Settings(Settings.FIND_STRING))
        findText.tooltip = Strings("TOOLTIP: Search for this string")
        findText.tooltipDescription = Strings("TOOLTIP TEXT: Search for this string")
        EventRegistry.register(findText, lambda input: Settings.Set(Settings.FIND_STRING, input.value))
        #endregion

        #region Replace string input
        replaceText = group.children.addStringValueInput(cls._REPLACE_STRING_ID, Strings("Replace with this string"), Settings(Settings.REPLACE_STRING))
        replaceText.tooltip = Strings("TOOLTIP: Replace with this string")
        replaceText.tooltipDescription = Strings("TOOLTIP TEXT: Replace with this string")
        EventRegistry.register(replaceText, lambda input: Settings.Set(Settings.REPLACE_STRING, input.value))
        #endregion

        #region Only selected Setups checkbox
        replaceOnlySelected = group.children.addBoolValueInput(cls._REPLACE_ONLY_SELECTED_ID, Strings("Only selected Setups"),  True, "", Settings(Settings.REPLACE_ONLY_SELECTED))
        replaceOnlySelected.tooltip = Strings("TOOLTIP: Only selected Setups")
        replaceOnlySelected.tooltipDescription = Strings("TOOLTIP TEXT: Only selected Setups")
        EventRegistry.register(replaceOnlySelected, lambda input: Settings.Set(Settings.REPLACE_ONLY_SELECTED, input.value))
        #endregion

        #region Replace button
        replaceButton = group.children.addBoolValueInput(cls._REPLACE_ID, "   " + Strings("Search and replace") + "   ", False) #l-/rjust() to widen the button some
        replaceButton.isFullWidth = True
        replaceButton.tooltip = Strings("TOOLTIP: Search and replace")
        replaceButton.tooltipDescription = Strings("TOOLTIP TEXT: Search and replace")
        
        def replaceButtonHandler(input: adsk.core.BoolValueCommandInput):
            values = input.parentCommand.commandInputs
            if input.value:
                Setups.RenameSetups(
                    values.itemById(cls._FIND_STRING_ID).value, 
                    values.itemById(cls._REPLACE_STRING_ID).value, 
                    values.itemById(cls._USE_REGEX_ID).value, 
                    values.itemById(cls._REPLACE_ONLY_SELECTED_ID).value
                )
                input.value = False # reset button state after operation

        EventRegistry.register(replaceButton, replaceButtonHandler)
        EventRegistry.register(replaceButton, lambda input: InputTab._updateSetups(input))
        #endregion
