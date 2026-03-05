from __future__ import annotations

from typing import cast

from adsk.core import (
    CommandInput,
    CommandInputs,
    DropDownCommandInput,
    DropDownStyles
)

from adsk.cam import Tool
from ...dialog.event_registry import EventRegistry

from .....lib.fusionParameters.cast_cam_param import castCAMParam

from ...programs import Programs
from ...setups.setups_context import SetupsContext
from ...strings import Strings

from ..constants import Constants

class ToolsTab(Constants):

    @classmethod
    def create(cls, ctx: SetupsContext, inputs: CommandInputs):
        
        # helper method to make the syntax a little easier for adding 
        # items to a table.
        def init(obj, **attrs):
            for k, v in attrs.items():
                setattr(obj, k, v)
            return obj

        #region ----- [ Tools tab ] -----
        toolsTab = inputs.addTabCommandInput(cls.TOOLS_GROUP_ID, Strings("Tools"))

        def _setTabEnabled(input: CommandInput):
            input.parentCommand.commandInputs.itemById(cls.TOOLS_GROUP_ID).isEnabled = Programs.Current is not None

        EventRegistry.register(cls.PROGRAM_DROPDOWN_ID, _setTabEnabled)
        _setTabEnabled(inputs.itemById(cls.PROGRAM_DROPDOWN_ID)) # initialize state based on current program selection



        input = toolsTab.children.addTableCommandInput(cls.TOOLS_TABLE_ID, '',4, "10:65:5:20") # 100% is easier to handle when redistributing the width
        input.minimumVisibleRows = 2
        input.maximumVisibleRows = 12
        input.hasGrid = False
        input.columnSpacing = 0
        input.isFullWidth = True
        row = 0
        # Add header row
        input.addCommandInput(
                init(inputs.addStringValueInput('', '', Strings('Tool ID')),
                isEnabled = False,
                isReadOnly = True,
                tooltip = Strings('Tool ID')
            ),row, 0)
        input.addCommandInput(
                init(inputs.addStringValueInput('', '', Strings('Tool Name')),
                isReadOnly = True,
                tooltip = Strings('Tool Name')
            ),row, 1)
        input.addCommandInput(
                init(inputs.addStringValueInput('', '', Strings('ATC Slot')),
                isReadOnly = True,
                tooltip = Strings('The slot in the automatic tool changer')
            ),row, 2, 0, 2)
        row += 1

        def _getToolNumber(tool: Tool) -> int:
            return castCAMParam.ToInt(tool.parameters.itemByName("tool_number"))

        def _requiresManualToolChange(tool: Tool) -> bool:
            return castCAMParam.ToBool(tool.parameters.itemByName('tool_manualToolChange'))
        
        def _getToolDescription(tool: Tool) -> str:
            return castCAMParam.ToStr(tool.parameters.itemByName('tool_description'))

        for tool in ctx.getTools():
            toolNumber = _getToolNumber(tool)
            dropdown = DropDownCommandInput.cast(inputs.addDropDownCommandInput(f"toolDropdown_{row}", '', cast(DropDownStyles, DropDownStyles.TextListDropDownStyle)))
            if Programs.Current is not None and Programs.Current.machineHasATC and not _requiresManualToolChange(tool):
                for i in range(1, Programs.Current.machineToolSlots + 1):
                    dropdown.listItems.add(str(i), toolNumber == i)
            dropdown.isEnabled = True

            input.addCommandInput(
                    init(inputs.addStringValueInput(f"toolNumber_{row}", '', str(toolNumber)),
                        isReadOnly = True
                ),row,0)
            input.addCommandInput(
                    init(inputs.addStringValueInput(f"tool_description_{row}", '', _getToolDescription(tool)),
                        isReadOnly = True
                ),row,1)
            input.addCommandInput(init(inputs.addBoolValueInput(f"toolCheckbox_{row}", '', True, '', False),
                    tooltip = Strings('Specify a custom tool number for this tool')
                                       ), row, 2)
            input.addCommandInput(dropdown, row, 3)
            row += 1



