from typing import cast

from adsk.core import BoolValueCommandInput
from adsk.core import CommandInputs
from adsk.core import CommandInput
from adsk.core import DropDownStyles
from adsk.core import DropDownCommandInput
from adsk.core import StringValueCommandInput

from ...settings.settings import Settings
from ...strings import Strings
from ...programs import Programs

from ...setups.setups_context import SetupsContext

from ..event_registry import EventRegistry
from ..constants import Constants

from .input_tab import InputTab

class MiscTab(Constants):
    @classmethod
    def create(cls, inputs: CommandInputs, ctx: SetupsContext):

        miscTab = inputs.addTabCommandInput(cls.RENAME_SETUPS_GROUP_ID, Strings("Misc"))

        def setTabEnabled(input: CommandInput):
            input.parentCommand.commandInputs.itemById(cls.OUTPUT_GROUP_ID).isEnabled = Programs.Current is not None

        EventRegistry.register(cls.PROGRAM_DROPDOWN_ID, setTabEnabled)
        setTabEnabled(inputs.itemById(cls.PROGRAM_DROPDOWN_ID)) # initialize state based on current program selection

        #region Language dropdown
        languageDropdown = miscTab.children.addDropDownCommandInput(cls.LANGUAGE_ID, Strings("Language"), cast(DropDownStyles, DropDownStyles.TextListDropDownStyle))
        languageDropdown.tooltip = Strings("TOOLTIP: Language")
        languageDropdown.tooltipDescription = (Strings("TOOLTIP TEXT: Language {fileVersion}")).format(fileVersion = Strings.file_version)

        languageTexts = Strings.available_languages()

        for language in languageTexts:
            languageDropdown.listItems.add(languageTexts[language], language == Settings(Settings.LANGUAGE))

        EventRegistry.register(cls.LANGUAGE_ID, lambda dropdown: Settings(Settings.LANGUAGE, Strings.language_setting(dropdown.selectedItem.name)))
        #endregion


        group = miscTab.children.addGroupCommandInput(cls.RENAME_SETUPS_GROUP_ID, Strings("Rename Setups"))
        group.isExpanded = True

        #region Use regex checkbox
        useRegex = group.children.addBoolValueInput(cls.USE_REGEX_ID, Strings("Use Python regular expressions"), True, "", bool(Settings(Settings.USE_REGEX)))
        useRegex.tooltip = Strings("TOOLTIP: Use Python regular expressions")
        useRegex.tooltipDescription = Strings("TOOLTIP TEXT: Use Python regular expressions")

        EventRegistry.register(cls.USE_REGEX_ID, lambda input: Settings.set(Settings.USE_REGEX, input.value))
        #endregion

        #region Find string input
        findText = group.children.addStringValueInput(cls.FIND_STRING_ID, Strings("Search for this string"), str(Settings(Settings.FIND_STRING)))
        findText.tooltip = Strings("TOOLTIP: Search for this string")
        findText.tooltipDescription = Strings("TOOLTIP TEXT: Search for this string")
        EventRegistry.register(cls.FIND_STRING_ID, lambda input: Settings.set(Settings.FIND_STRING, input.value))
        #endregion

        #region Replace string input
        replaceText = group.children.addStringValueInput(cls.REPLACE_STRING_ID, Strings("Replace with this string"), Settings(Settings.REPLACE_STRING))
        replaceText.tooltip = Strings("TOOLTIP: Replace with this string")
        replaceText.tooltipDescription = Strings("TOOLTIP TEXT: Replace with this string")
        EventRegistry.register(cls.REPLACE_STRING_ID, lambda input: Settings.set(Settings.REPLACE_STRING, input.value))
        #endregion

        #region Only selected Setups checkbox
        replaceOnlySelected = group.children.addBoolValueInput(cls.REPLACE_ONLY_SELECTED_ID, Strings("Only selected Setups"),  True, "", Settings(Settings.REPLACE_ONLY_SELECTED))
        replaceOnlySelected.tooltip = Strings("TOOLTIP: Only selected Setups")
        replaceOnlySelected.tooltipDescription = Strings("TOOLTIP TEXT: Only selected Setups")
        EventRegistry.register(cls.REPLACE_ONLY_SELECTED_ID, lambda input: Settings.set(Settings.REPLACE_ONLY_SELECTED, input.value))
        #endregion

        #region Replace button
        replaceButton = group.children.addBoolValueInput(cls.REPLACE_ID, "   " + Strings("Search and replace") + "   ", False) #l-/rjust() to widen the button some
        replaceButton.isFullWidth = True
        replaceButton.tooltip = Strings("TOOLTIP: Search and replace")
        replaceButton.tooltipDescription = Strings("TOOLTIP TEXT: Search and replace")
        
        def replaceButtonHandler(input: BoolValueCommandInput):
            values = input.parentCommand.commandInputs
            if input.value:
                ctx.rename_setups(
                    StringValueCommandInput.cast(values.itemById(cls.FIND_STRING_ID)).value, 
                    StringValueCommandInput.cast(values.itemById(cls.REPLACE_STRING_ID)).value, 
                    BoolValueCommandInput.cast(values.itemById(cls.USE_REGEX_ID)).value, 
                    BoolValueCommandInput.cast(values.itemById(cls.REPLACE_ONLY_SELECTED_ID)).value
                )
                input.value = False # reset button state after operation

        EventRegistry.register(cls.REPLACE_ID, replaceButtonHandler)
        EventRegistry.register(cls.REPLACE_ID, lambda input: InputTab._updateSetups(input, ctx))
        #endregion
