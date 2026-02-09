from adsk.core import DropDownStyles

from ...programs import Programs
from ...setups.setups import Setups
from ...strings import Strings


class InputTab():
    @classmethod
    def createInputTab(cls, inputs):

        # helper method to make the syntax a little easier for adding 
        # items to a table.
        def init(obj, **attrs):
            for k, v in attrs.items():
                setattr(obj, k, v)
            return obj
        
        #region ----- [ Input tab ] -----
        inputTab = inputs.addTabCommandInput(cls._INPUT_SELECTION_TAB_ID, Strings("Input Selection"))
        inputTab.activate()

        #region Program dropdown
        input = inputTab.children.addDropDownCommandInput(cls._PROGRAM_DROPDOWN_ID, Strings('NC Program'), DropDownStyles.TextListDropDownStyle)
        input.tooltip = Strings("TOOL TIP: NC Program to Use")
        input.tooltipDescription = Strings("TOOLTIP TEXT: NC Program to Use")
        for program in Programs:
            if not program.hasError and not program.isEmpty and not program.isSuppressed:
                input.listItems.add(program.name, False)
        input.isEnabled = True
        #endregion

        #region Program machine text field
        input = inputTab.children.addStringValueInput(cls._MACHINE_ID, Strings('Machine'), Strings('<Select program>'))
        input.tooltip = Strings("TOOL TIP: Machine")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Machine")
        input.isReadOnly = True
        input.isEnabled = False
        #endregion

        #region Post Processor text field
        input = inputTab.children.addStringValueInput(cls._POST_PROCESSOR_ID, Strings('Post Processor'), Strings('<Select program>'))
        input.tooltip = Strings("TOOL TIP: Post Processor")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Post Processor")
        input.isReadOnly = True
        input.isEnabled = False
        #endregion

        #region Setups table
        input = inputTab.children.addTableCommandInput('SetupsTable', '',5, "1:7:3:3:3")
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
        
        # Add setup rows
        for setup in Setups:
            row += 1
            input.addCommandInput(
                inputs.addBoolValueInput(f"setupSelected_{setup.index}", '', True, '', setup.isSelected),row,0)
            input.addCommandInput(
                init(inputs.addStringValueInput(f"setupName_{setup.index}", '', setup.name),
                    isReadOnly = True,
                    isEnabled = setup.isSelected
                ),row,1)
            input.addCommandInput(
                init(inputs.addStringValueInput(f"setupOrigin_{setup.index}", '', ''),
                    isReadOnly = True,
                    isEnabled = setup.isSelected
                ),row,2)
            input.addCommandInput(
                init(inputs.addStringValueInput(f"setupXNormal_{setup.index}", '', ''),
                    isReadOnly = True,
                    isEnabled = setup.isSelected
                ),row,3)
            input.addCommandInput(
                init(inputs.addStringValueInput(f"setupARotation_{setup.index}", '', ''),
                    isReadOnly = True,
                    isEnabled = setup.isSelected
                ),row,4)
        #endregion
        #endregion -----
