import adsk
from ...programs import Programs
from ...setups.setups import Setups
from ...strings import Strings

from ..dialog_constants import PostDialogConstants

class ToolsTab(PostDialogConstants):

    _TOOLS_GROUP_ID = 'toolsTab'
    _TOOLS_TABLE_ID = 'toolsTable'

    @classmethod
    def createToolsTab(cls, inputs: adsk.core.CommandInputs):

        # helper method to make the syntax a little easier for adding 
        # items to a table.
        def init(obj, **attrs):
            for k, v in attrs.items():
                setattr(obj, k, v)
            return obj

        #region ----- [ Tools tab ] -----
        toolsTab = inputs.addTabCommandInput(cls._TOOLS_GROUP_ID, Strings("Tools"))
        toolsTab.isEnabled = True

        input = toolsTab.children.addTableCommandInput(cls._TOOLS_TABLE_ID, '',4, "10:65:5:20")
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



        for tool in Setups.tools:
            toolNumber = tool.parameters.itemByName("tool_number").value.value
            dropdown: adsk.core.DropDownCommandInput = inputs.addDropDownCommandInput(f"toolDropdown_{row}", '', adsk.core.DropDownStyles.TextListDropDownStyle)
            if Programs.Current is not None and Programs.Current.machineHasATC and tool.parameters.itemByName('tool_manualToolChange').value.value == False:
                for i in range(1, Programs.Current.machineToolSlots + 1):
                    dropdown.listItems.add(str(i), toolNumber == i)
            dropdown.isEnabled = True
            dropdown.isReadOnly = True

            input.addCommandInput(
                    init(inputs.addStringValueInput(f"toolNumber_{row}", '', str(toolNumber)),
                        isReadOnly = True
                ),row,0)
            input.addCommandInput(
                    init(inputs.addStringValueInput(f"tool_description_{row}", '', tool.parameters.itemByName("tool_description").value.value),
                        isReadOnly = True
                ),row,1)
            input.addCommandInput(init(inputs.addBoolValueInput(f"toolCheckbox_{row}", '', True, '', False),
                    tooltip = Strings('Specify a custom tool number for this tool')
                                       ), row, 2)
            input.addCommandInput(dropdown, row, 3)
            row += 1



