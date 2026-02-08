import adsk
from adsk.core import DropDownStyles

from ..programs import Programs
from ..setups.setups import Setups
from ..settings import Settings
from ..strings import Strings

class PostDialogLayout:
    
    @classmethod
    def createLayout(cls, command: adsk.core.Command):

        command.setDialogMinimumSize(465, 580)
        command.setDialogInitialSize(465, 580)
        command.okButtonText = Strings("Process")
        command.cancelButtonText = Strings("Close")

        # helper method to make the syntax a little easier for adding 
        # items to a table.
        def init(obj, **attrs):
            for k, v in attrs.items():
                setattr(obj, k, v)
            return obj

        # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
        inputs = command.commandInputs

        #region - [ Dialog layout definitions ] -----------------------

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

        #region ----- [ G-code tab ] -----

        gCodeTab = inputs.addTabCommandInput(cls._GCODE_OPTIONS_GROUP_ID, Strings("G-code options"))
        gCodeTab.isEnabled = False

        #region Tool change string input
        input = gCodeTab.children.addTextBoxCommandInput(cls._TOOL_CHANGE_ID, Strings('Tool change code'), Settings(Settings.TOOL_CHANGE), 3, False)
        input.tooltip = Strings("TOOL TIP: Tool change code")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Tool change code")
        #endregion

        #region dummy input to separate the textboxes properly
        dummy = gCodeTab.children.addStringValueInput('dummy', '')
        dummy.isEnabled = False
        dummy.isReadOnly = True
        #endregion

        #region Body end codes textbox input
        input = gCodeTab.children.addTextBoxCommandInput(cls._END_CODES_ID, Strings('G-codes that mark ending sequence'), Settings(Settings.END_CODES), 3, False)
        input.tooltip = Strings("TOOL TIP: G-codes that mark ending sequence")
        input.tooltipDescription = Strings("TOOLTIP TEXT: G-codes that mark ending sequence")

        dummy = gCodeTab.children.addBoolValueInput('','', True, "", False) # As the TextBoxCommandInput above seems to be buggy we add a dummy input to create some space
        dummy.isEnabled = False
        #endregion

        #region Header end codes textbox input
        input = gCodeTab.children.addTextBoxCommandInput(cls._HEADER_CODES_ID, Strings('G-codes that mark header end'), Settings(Settings.HEADER_END_CODES), 3, False)
        input.tooltip = Strings("TOOL TIP: G-codes that mark header end")
        input.tooltipDescription = Strings("TOOLTIP TEXT: G-codes that mark header end")

        dummy = gCodeTab.children.addBoolValueInput('','', True, "", False) # As the TextBoxCommandInput above seems to be buggy we add a dummy input to create some space
        dummy.isEnabled = False
        #endregion

        #region Restore rapid moves checkbox
        input = gCodeTab.children.addBoolValueInput(cls._RESTORE_RAPID_MOVES_ID,Strings('Restore rapid moves'), True, "", Settings(Settings.RESTORE_RAPID_MOVES))
        input.tooltip = Strings("TOOL TIP: Restore rapid moves")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Restore rapid moves")
        #endregion
        #endregion -----

        #region ----- [ Output tab ] -----
        outputTab = inputs.addTabCommandInput(cls._OUTPUT_GROUP_ID, Strings("Output Options"))
        outputTab.isEnabled = False

        #region -- Output folder table --
        input = outputTab.children.addTableCommandInput(cls._OUTPUT_FOLDER_TABLE_ID, Strings('Output folder'), 2, '12:1')
        input.minimumVisibleRows = 2
        input.maximumVisibleRows = 2
        input.tablePresentationStyle = adsk.core.TablePresentationStyles.transparentBackgroundTablePresentationStyle

        #region Output folder label, spans 2 columns
        input.addCommandInput(
            init(inputs.addStringValueInput(cls._OUTPUT_FOLDER_LABEL_ID, '', Strings("Output folder")), 
                tooltip = Strings("TOOL TIP: Output folder"),
                tooltipDescription = Strings("TOOLTIP TEXT: Output folder"),
                isReadOnly = True
            ), 0, 0, 0, 2)
        #endregion

        #region Output folder string input
        input.addCommandInput(
            init(inputs.addStringValueInput(cls._OUTPUT_FOLDER_ID, Strings("Output folder"), Strings("<Select program>")),
                tooltip = Strings("TOOL TIP: Output folder"),
                tooltipDescription = Strings("TOOLTIP TEXT: Output folder"),
                isReadOnly = False
            ), 1, 0)
        #endregion

        #region Output folder browse button
        input.addCommandInput(inputs.addBoolValueInput(cls._OUTPUT_FOLDER_BUTTON_ID, '  …  ', False, '', False), 1, 1)
        #endregion
        #endregion

        #region File name string input
        input = outputTab.children.addStringValueInput(cls._FILE_NAME_ID, Strings("File name"), Strings("<Select program>"))
        input.tooltip = Strings("TOOL TIP: File name")
        input.tooltipDescription = Strings("TOOLTIP TEXT: File name")
        #endregion

        #region Numeric name checkbox
        input = outputTab.children.addBoolValueInput(cls._NUMERIC_NAME_ID, Strings("Name must be numeric"), True, "", Settings(Settings.NUMERIC_NAME))
        input.tooltip = Strings("TOOL TIP: Name must be numeric")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Name must be numeric")
        #endregion

        #region Prepend sequence number dropdown
        input = outputTab.children.addDropDownCommandInput(cls._PREPEND_SEQUENCE_ID, Strings("Prepend sequence number"), adsk.core.DropDownStyles.TextListDropDownStyle)
        input.tooltip = Strings("TOOL TIP: Prepend sequence number")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Prepend sequence number")
        input.listItems.add(Strings("File names only"), input.listItems.count == Settings(Settings.SEQUENCE))
        input.listItems.add(Strings("Operation steps only"), input.listItems.count == Settings(Settings.SEQUENCE))
        input.listItems.add(Strings("File names and operation steps"), input.listItems.count == Settings(Settings.SEQUENCE))
        input.listItems.add(Strings("None"), input.listItems.count == Settings(Settings.SEQUENCE))
        #endregion

        #region Numbering digits spinner input
        input = outputTab.children.addIntegerSpinnerCommandInput(cls._DIGITS_COUNT_ID, Strings("Numbering digits"), 1, 6, 1, Settings(Settings.NAME_DIGITS))
        input.tooltip = Strings("TOOL TIP: Numbering digits")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Numbering digits")
        #endregion

        #region Numbering interval spinner input
        input = outputTab.children.addIntegerSpinnerCommandInput(cls._NUMBERING_INTERVAL_ID, Strings("Numbering interval"), 1, 6, 1, Settings(Settings.NUMBERING_INTERVAL))
        input.tooltip = Strings("TOOL TIP: Numbering interval")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Numbering interval")
        #endregion

        #region Combine tool checkbox
        input = outputTab.children.addBoolValueInput(cls._COMBINE_TOOLS_ID, Strings('Combine operations using same tool'), True, "", Settings(Settings.COMBINE_TOOL))
        input.tooltip = Strings("TOOL TIP: Combine operations using same tool")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Combine operations using same tool")
        #endregion

        #region Rotate A-Axis between setups checkbox
        input = outputTab.children.addBoolValueInput(cls._ROTATE_A_AXIS_ID, Strings('Rotate A-Axis between setups'), True, "", Settings(Settings.ROTATE_A_AXIS))
        input.tooltip = Strings("TOOL TIP: Rotate A-Axis between setups")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Rotate A-Axis between setups")
        #endregion

        #region Retract to safe Y on A-axis rotation checkbox
        input = outputTab.children.addBoolValueInput(cls._SAFE_Y_RETRACTION_ID, Strings("Retract Y on A-axis rotation"), True, "", Settings(Settings.SAFE_Y_RETRACTION))
        input.tooltip = Strings("TOOL TIP: Retract Y on A-axis rotation")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Retract Y on A-axis rotation")
        #endregion

        #region Safe Y-retraction coordinate number
        input = outputTab.children.addIntegerSpinnerCommandInput(cls._Y_RETRACTION_COORDINATE_ID, Strings("Safe Y-retraction coordinate (mm)"), -150, 0, 1, Settings(Settings.Y_RETRACTION_COORDINATE))
        input.tooltip = Strings("TOOL TIP: Safe Y-retraction coordinate (mm)")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Safe Y-retraction coordinate (mm)")
        #endregion

        #region Operations grouping dropdown
        input = outputTab.children.addDropDownCommandInput(cls._OPERATIONS_GROUPING_ID, Strings("Operations grouping"), adsk.core.DropDownStyles.TextListDropDownStyle)
        input.tooltip = Strings("TOOL TIP: Operations grouping")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Operations grouping")

        #endregion

        #region Flat file structure checkbox
        input = outputTab.children.addBoolValueInput(cls._FLAT_FILE_STRUCTURE_ID, Strings("Flat file structure"), True, "", Settings(Settings.FLAT_FILE_STRUCTURE))
        input.tooltip = Strings("TOOL TIP: Flatten the file structure")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Flatten the file structure")
        #endregion

        #region Delete existing files checkbox
        input = outputTab.children.addBoolValueInput(cls._DELETE_EXISTING_FILES_ID, Strings("Delete existing files"),  True, "", Settings(Settings.DEL_FILES))
        input.tooltip = Strings("TOOL TIP: Delete existing files")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Delete existing files")
        input.isEnabled = False
        #endregion

        #region Delete output folder checkbox
        input = outputTab.children.addBoolValueInput(cls._DELETE_OUTPUT_FOLDER_ID, Strings("Delete output folder"),  True, "", Settings(Settings.DEL_FOLDER))
        input.tooltip = Strings("TOOL TIP: Delete output folder")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Delete output folder")
        #endregion -----
        #endregion

        #region ----- [ Misc tab ] -----
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
        #endregion

        #region Save as default button
        input = inputs.addSeparatorCommandInput('dummy')

        input = inputs.addBoolValueInput(cls._SAVE_ID, f"   {Strings("Save as default settings")}   ", False)
        input.tooltip = Strings("TOOL TIP: Save as default settings")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Save as default settings")
        input.isFullWidth = True
        input.isEnabled = False
        #endregion

        #endregion ----------------------------------------------------

        programDropdown: adsk.core.DropDownCommandInput = inputs.itemById(cls._PROGRAM_DROPDOWN_ID)
        selectedItem = next((listItem for listItem in programDropdown.listItems if listItem.name == Settings(Settings.NC_PROGRAM)), None)
        if selectedItem != None and not selectedItem.isSelected:
            selectedItem.isSelected = True
