import adsk
from ...strings import Strings

class ToolsTab:

    _TOOLS_GROUP_ID = 'toolsTab'

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

        input = toolsTab.children.addTableCommandInput('SetupsTable', '',5, "1:7:3:3:3")
        input.minimumVisibleRows = 3
        input.maximumVisibleRows = 12
        row = 0
        # Add header row
        input.addCommandInput(
                init(inputs.addBoolValueInput(cls._SELECT_ALL_SETUPS_ID, '', True, '', False),
                     value = False
            ),row,0)
        input.addCommandInput(
                init(inputs.addStringValueInput('', '', Strings('Setup Name')),
                isReadOnly = True
            ),row,1)
        input.addCommandInput(
                init(inputs.addStringValueInput('', '', Strings('Origin')),
                isReadOnly = True
            ),row,2)
        input.addCommandInput(
                init(inputs.addStringValueInput('', '', Strings('X-axis')),
                isReadOnly = True
            ),row,3)
        input.addCommandInput(
                init(inputs.addStringValueInput('', '', Strings('Rotation')),
                isReadOnly = True
            ),row,4)
