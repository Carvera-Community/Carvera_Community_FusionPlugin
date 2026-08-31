from adsk.core import BoolValueCommandInput, DropDownStyles

from ...programs import Programs
from ...settings.settings import Settings
from ...strings import Strings
from ..event_registry import EventRegistry
from ..state import can_combine_tools


def create_grouping_and_safety_options(output_tab, constants) -> None:
    grouping_input = output_tab.children.addDropDownCommandInput(
        constants.OPERATIONS_GROUPING_ID,
        Strings("Operations grouping"),
        DropDownStyles.TextListDropDownStyle,
    )
    grouping_input.tooltip = Strings("TOOLTIP: Operations grouping")
    grouping_input.tooltipDescription = Strings("TOOLTIP TEXT: Operations grouping")
    grouping_values = {
        Strings("Single file"): Settings.OperationsGroupings.SINGLE_FILE,
        Strings("Group on setup"): Settings.OperationsGroupings.SETUP,
        Strings("Group on setup and tool"): Settings.OperationsGroupings.SETUP_AND_TOOL,
        Strings("None, one file per operation"): Settings.OperationsGroupings.PER_OPERATION,
    }
    for label, value in grouping_values.items():
        grouping_input.listItems.add(
            label,
            value == Settings(Settings.OPERATIONS_GROUPING),
        )
    EventRegistry.register(
        constants.OPERATIONS_GROUPING_ID,
        lambda dropdown: Settings.set(
            Settings.OPERATIONS_GROUPING,
            grouping_values[dropdown.selectedItem.name],
        ),
    )

    combine_tools = output_tab.children.addBoolValueInput(
        constants.COMBINE_TOOLS_ID,
        Strings("Combine operations using same tool"),
        True,
        "",
        Settings(Settings.COMBINE_TOOL),
    )
    combine_tools.tooltip = Strings("TOOLTIP: Combine operations using same tool")
    combine_tools.tooltipDescription = Strings("TOOLTIP TEXT: Combine operations using same tool")
    EventRegistry.register(
        constants.COMBINE_TOOLS_ID,
        lambda checkbox: Settings(Settings.COMBINE_TOOL, checkbox.value),
    )

    def update_combine_tools(dropdown) -> None:
        grouping = grouping_values[dropdown.selectedItem.name]
        enabled = can_combine_tools(grouping, Settings.OperationsGroupings)
        combine_tools.isEnabled = enabled
        if not enabled:
            combine_tools.value = False
            Settings(Settings.COMBINE_TOOL, False)

    EventRegistry.register(constants.OPERATIONS_GROUPING_ID, update_combine_tools)
    update_combine_tools(grouping_input)

    flat_structure = output_tab.children.addBoolValueInput(
        constants.FLAT_FILE_STRUCTURE_ID,
        Strings("Flat file structure"),
        True,
        "",
        Settings(Settings.FLAT_FILE_STRUCTURE),
    )
    flat_structure.tooltip = Strings("TOOLTIP: Flatten the file structure")
    flat_structure.tooltipDescription = Strings("TOOLTIP TEXT: Flatten the file structure")
    EventRegistry.register(
        constants.FLAT_FILE_STRUCTURE_ID,
        lambda checkbox: Settings.set(Settings.FLAT_FILE_STRUCTURE, checkbox.value),
    )

    overwrite = output_tab.children.addBoolValueInput(
        constants.OVERWRITE_EXISTING_FILES_ID,
        Strings("Overwrite existing files"),
        True,
        "",
        Settings(Settings.OVERWRITE_FILES),
    )
    overwrite.tooltip = Strings("TOOLTIP: Overwrite existing files")
    overwrite.tooltipDescription = Strings("TOOLTIP TEXT: Overwrite existing files")
    overwrite.isEnabled = True
    EventRegistry.register(
        constants.OVERWRITE_EXISTING_FILES_ID,
        lambda checkbox: Settings(Settings.OVERWRITE_FILES, checkbox.value),
    )

    clear_folder = output_tab.children.addBoolValueInput(
        constants.CLEAR_OUTPUT_FOLDER_ID,
        Strings("Clear output folder"),
        True,
        "",
        Settings(Settings.CLEAR_FOLDER),
    )
    clear_folder.tooltip = Strings("TOOLTIP: Clear output folder")
    clear_folder.tooltipDescription = Strings("TOOLTIP TEXT: Clear output folder")

    def update_clear_folder(checkbox: BoolValueCommandInput):
        clear_input = BoolValueCommandInput.cast(
            checkbox.parentCommand.commandInputs.itemById(constants.CLEAR_OUTPUT_FOLDER_ID)
        )
        clear_input.isEnabled = checkbox.value
        if not checkbox.value:
            Settings(Settings.CLEAR_FOLDER, False)
            clear_input.value = False

    EventRegistry.register(
        constants.CLEAR_OUTPUT_FOLDER_ID,
        lambda checkbox: Settings.set(Settings.CLEAR_FOLDER, checkbox.value),
    )
    EventRegistry.register(constants.OVERWRITE_EXISTING_FILES_ID, update_clear_folder)
    update_clear_folder(overwrite)
