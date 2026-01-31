from __future__ import annotations
from pathlib import Path
import tempfile
import adsk.core
from adsk.core import DropDownStyles
import os

from .setup import Setup
from .setups import Setups
from .parameters import Parameters
from .programs import Programs
from .settings import Settings
from .strings import Strings

from .const import Const
from ...lib.fusionAddInUtils.general_utils import Utils
from ...lib.fusionAddInUtils.event_utils import Events
from . import config

class PostDialog:

    # Local list of event handlers used to maintain a reference so
    # they are not released and garbage collected.
    _local_handlers = []

    # Resource location for command icons, here we assume a sub folder in this directory named "resources".
    _ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

    #region Input id's
    _PROGRAM_DROPDOWN_ID = 'program'
    _OUTPUT_FOLDER_ID = 'outputFolder'
    _COMBINE_TOOLS_ID = 'combineTool'
    _TOOL_CHANGE_ID = 'toolChange'
    _END_CODES_ID = 'endCodes'
    _RESTORE_RAPID_MOVES_ID = 'restoreRapidMoves'
    _DELETE_OUTPUT_FOLDER_ID = 'deleteOutputFolder'
    _OPERATIONS_GROUPING_ID = 'operationsGrouping'
    _DELETE_EXISTING_FILES_ID = 'deleteExistingFiles'
    _PREPEND_SEQUENCE_ID = 'prependSequence'
    _DIGITS_COUNT_ID = 'digitsCount'
    _NUMBERING_INTERVAL_ID = 'numberingInterval'
    _USE_REGEX_ID = 'useRegex'
    _FIND_STRING_ID = 'findString'
    _REPLACE_STRING_ID = 'replaceString'
    _REPLACE_ID = 'replace'
    _INITIAL_DELAY_ID = 'initialDelay'
    _POST_RETRIES_ID = 'postRetries'
    _NUMERIC_NAME_ID = 'numericName'
    _SAVE_ID = 'saveAsDefault'
    _RENAME_SETUPS_GROUP_ID = 'renameSetupsGroup'
    _ADVANCED_SETTINGS_GROUP_ID = 'advancedSettingsGroup'
    _OUTPUT_GROUP_ID = 'outputGroup'
    _INPUT_SELECTION_TAB_ID = 'inputSelectionGroup'
    _GCODE_OPTIONS_GROUP_ID = 'gcodeOptionsGroup'
    _OUTPUT_FOLDER_LABEL_ID = 'outputFolderLabel'
    _OUTPUT_FOLDER_BUTTON_ID = 'outputFolderButton'
    _OUTPUT_FOLDER_TABLE_ID = 'outputFolderTable'
    _FLAT_FILE_STRUCTURE_ID = 'flatFileStructure'
    _MACHINE_ID = 'machine'
    _ROTATE_A_AXIS_ID = 'rotateAAxis'
    _SAFE_Y_RETRACTION_ID = 'safeYRetraction'
    _Y_RETRACTION_COORDINATE_ID = 'yRetractionCoordinate'
    _POST_PROCESSOR_ID = 'postProcessor'
    _FILE_NAME_ID = 'fileName'
    _HEADER_CODES_ID = 'headerEndCodes'
    _WCS_NOT_ALIGNED_ID = 'WCSNotAligned'
    #endregion

    # Executed when add-in is started.
    @staticmethod
    def start():
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # Create a command Definition.
        cmd_def = ui.commandDefinitions.addButtonDefinition( \
            config.CMD_ID, \
            config.CMD_NAME, \
            config.CMD_DESCRIPTION, \
            PostDialog._ICON_FOLDER \
        )

        # Define an event handler for the command created event. It will be called when the button is clicked.
        Events.add(cmd_def.commandCreated, PostDialog.commandCreated)

        # ******** Add a button into the UI so the user can run the command. ********
        # Get the target workspace the button will be created in.
        workspace = ui.workspaces.itemById(Const.CAM_WORKSPACE_ID)

        # Get the panel the button will be created in.
        panel = workspace.toolbarPanels.itemById(Const.CAM_ACTIONS_PANEL_ID)

        # Create the button command control in the UI after the specified existing command.
        control = panel.controls.addCommand(cmd_def, Const.POST_PROCESS_CONTROL_ID, False)

        # Specify if the command is promoted to the main toolbar. 
        control.isPromoted = True

    # Executed when add-in is stopped.
    @staticmethod
    def stop():
        # Get the various UI elements for this command
        app = adsk.core.Application.get()
        ui = app.userInterface

        workspace = ui.workspaces.itemById(Const.CAM_WORKSPACE_ID)
        panel = workspace.toolbarPanels.itemById(Const.CAM_ACTIONS_PANEL_ID)
        command_control = panel.controls.itemById(config.CMD_ID)
        command_definition = ui.commandDefinitions.itemById(config.CMD_ID)

        # Delete the button command control
        if command_control:
            command_control.deleteMe()

        # Delete the command definition
        if command_definition:
            command_definition.deleteMe()

    #
    # Event handlers
    #

    # Function that is called when a user clicks the corresponding button in the UI.
    # This defines the contents of the command dialog and connects to the command related events.
    @staticmethod
    def commandCreated(args: adsk.core.CommandCreatedEventArgs):
        # General logging for debug.
        Utils.log(f'{config.CMD_NAME} Command Created Event')

        app: adsk.core.Application = adsk.core.Application.get()
        doc: adsk.core.Document = app.activeDocument
        cam: adsk.cam.CAM = adsk.cam.CAM.cast(app.activeDocument.products.itemByProductType(Const.CAM_PRODUCT_ID))

        Settings.Load() # Load default settings
        Strings.set_language(Settings(Settings.LANGUAGE))  # Load language
        Programs.Load(cam) # Get the list of NCPrograms in the current document

        command = args.command

        PostDialog.createDialog(command)

    # This event handler is called when the user clicks the OK button in the command dialog or 
    # is immediately called after the created event not command inputs were created for the dialog.
    @staticmethod
    def command_execute(args: adsk.core.CommandEventArgs):
        # General logging for debug.
        Utils.log(f'{config.CMD_NAME} Command Execute Event')

        app: adsk.core.Application = adsk.core.Application.get()
        ui = app.userInterface
        command = args.command

        alignedWCS, badOrigins, badXAxes = Setups.getWCSAlignmentIssues()
        if not alignedWCS:
            Utils.log(f'PostDialog: WCS are not aligned for setups: {badOrigins}', adsk.core.LogLevels.ErrorLogLevel)
            msg = '<i><u>Warning:</u></i><p>'
            if command.commandInputs.itemById(PostDialog._ROTATE_A_AXIS_ID).value:
                msg += "Using 4th axis rotation while all Work Coordinate Systems isn't aligned properly may result in unexpected results, including damage to property and person.<p>"
            else:
                msg += "Some Work Coordinate Systems aren't aligned properly which may result in unexpected results, including damage to property and person.<p>"
            msg += "Do NOT use the result from this plug-in unless you have personally verified that the result can be used.<p>" 
            res = ui.messageBox(msg,
            "WARNING! Do not proceed!", 
            adsk.core.MessageBoxButtonTypes.OKCancelButtonType,
            adsk.core.MessageBoxIconTypes.CriticalIconType)
        
            if res != adsk.core.DialogResults.DialogOK:
                Utils.log('PostDialog: User cancelled operation due to unaligned WCS.', adsk.core.LogLevels.InfoLogLevel)
                return


        if not Programs.Current.machineHasAAxis:
            needAAxisRotation, setups = Setups.AAxisRotationRequired()
            if needAAxisRotation:
                Utils.log(f'PostDialog: Machine {Programs.Current.MachineName} does not support A axis but setups {setups} require A axis rotation.', adsk.core.LogLevels.WarningLogLevel)
                msg = '<i><u>Warning:</u></i><p>'
                msg += f"The selected machine '{Programs.Current.MachineName}' does not support A axis rotation, but the following setups require A axis rotation:<p>"
                for setupName, angle in setups:
                    msg += f"{setupName} ({angle}°)<p>"
                msg += "Using 4th axis rotation while the machine doesn't support it may result in unexpected results, including damage to property and person.<p>"
                msg += "Do NOT use the result from this plug-in unless you have personally verified that the result can be used.<p>" 
                res = ui.messageBox(msg,
                "WARNING! Do not proceed!", 
                adsk.core.MessageBoxButtonTypes.OKCancelButtonType,
                adsk.core.MessageBoxIconTypes.CriticalIconType)
            
                if res != adsk.core.DialogResults.DialogOK:
                    Utils.log('PostDialog: User cancelled operation due to unsupported A axis rotation.', adsk.core.LogLevels.InfoLogLevel)
                    return


        if Programs.Current is not None:
            Settings.Save(Programs.Current.attributes)  # Save settings for the current project
        else:
            app: adsk.core.Application = adsk.core.Application.get()
            doc: adsk.core.Document = app.activeDocument
            Settings.Save(doc.attributes)  # Save settings for the current project


        # Create a temporary folder to prepare all files in
        with tempfile.TemporaryDirectory() as tmpdir:
            Programs.Current.Process(Path(tmpdir))
            Programs.Current.Generate()

    # This event handler is called when the command needs to compute a new preview in the graphics window.
    @staticmethod
    def command_preview(args: adsk.core.CommandEventArgs):
        # General logging for debug.
        Utils.log(f'{PostDialog._CMD_NAME} Command Preview Event')

    # This event handler is called when the user changes anything in the command dialog
    # allowing you to modify values of other inputs based on that change.
    @staticmethod
    def commandInputChanged(args: adsk.core.InputChangedEventArgs):
        if PostDialog.mouseDown:
            return 
        
        changedInput = args.input

        if changedInput.id == PostDialog._PROGRAM_DROPDOWN_ID:
            PostDialog.onProgramChanged(changedInput)
        
        elif changedInput.id == PostDialog._TOOL_CHANGE_ID:
            PostDialog.onToolChangeChanged(changedInput)

        elif changedInput.id == PostDialog._END_CODES_ID:
            PostDialog.onEndCodesChanged(changedInput)

        elif changedInput.id == PostDialog._RESTORE_RAPID_MOVES_ID:
            PostDialog.onRestoreRapidMovesChanged(changedInput)

        elif changedInput.id == PostDialog._OUTPUT_FOLDER_ID:
            PostDialog.onOutputFolderChanged(changedInput)
        
        elif changedInput.id == PostDialog._OUTPUT_FOLDER_BUTTON_ID:
            PostDialog.onOutputFolderButtonChanged(changedInput)

        elif changedInput.id == PostDialog._NUMERIC_NAME_ID:
            PostDialog.onNumericNameChanged(changedInput)

        elif changedInput.id == PostDialog._PREPEND_SEQUENCE_ID:
            PostDialog.onPrependSequenceChanged(changedInput)
            
        elif changedInput.id == PostDialog._DIGITS_COUNT_ID:
            PostDialog.onDigitsCountChanged(changedInput)
        
        elif changedInput.id == PostDialog._COMBINE_TOOLS_ID:
            PostDialog.onCombineToolsChanged(changedInput)

        elif changedInput.id == PostDialog._ROTATE_A_AXIS_ID:
            PostDialog.onRotateAAxisChanged(changedInput)

        elif changedInput.id == PostDialog._SAFE_Y_RETRACTION_ID:
            PostDialog.onSafeYRetractionChanged(changedInput)

        elif changedInput.id == PostDialog._Y_RETRACTION_COORDINATE_ID:
            PostDialog.onYRetractionCoordinateChanged(changedInput)

        elif changedInput.id == PostDialog._OPERATIONS_GROUPING_ID:
            PostDialog.onOperationsGroupingChanged(changedInput)

        elif changedInput.id == PostDialog._FLAT_FILE_STRUCTURE_ID:
            PostDialog.onFlatFileStructureChanged(changedInput)

        elif changedInput.id == PostDialog._DELETE_EXISTING_FILES_ID:
            PostDialog.onDeleteExistingFilesChanged(changedInput)

        elif changedInput.id == PostDialog._DELETE_OUTPUT_FOLDER_ID:
            PostDialog.onDeleteOutputFolderChanged(changedInput)

        elif changedInput.id == PostDialog._USE_REGEX_ID:
            PostDialog.onUseRegexChanged(changedInput)

        elif changedInput.id == PostDialog._FIND_STRING_ID:
            PostDialog.onFindStringChanged(changedInput)

        elif changedInput.id == PostDialog._REPLACE_STRING_ID:
            PostDialog.onReplaceStringChanged(changedInput)

        elif changedInput.id == PostDialog._REPLACE_ID:
            PostDialog.onReplaceChanged(changedInput)

        elif changedInput.id == PostDialog._INITIAL_DELAY_ID:
            PostDialog.onInitialDelayChanged(changedInput)

        elif changedInput.id == PostDialog._POST_RETRIES_ID:
            PostDialog.onPostRetriesChanged(changedInput)
        
        elif changedInput.id == PostDialog._SAVE_ID:
            PostDialog.onSaveChanged(changedInput)

        elif changedInput.id == PostDialog._FILE_NAME_ID:
            PostDialog.onFileNameChanged(changedInput)

        elif changedInput.id.startswith('setupSelected_'):
            PostDialog.onSetupSelectedChanged(changedInput)
        
        # General logging for debug.
        Utils.log(f'{config.CMD_NAME} Input Changed Event fired from a change to {changedInput.id}')

    # This event handler is called when the user interacts with any of the inputs in the dialog
    # which allows you to verify that all of the inputs are valid and enables the OK button.
    @staticmethod
    def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
        # General logging for debug.
        Utils.log(f'{config.CMD_NAME} Validate Input Event')

        inputs = args.inputs
        
        # # Verify the validity of the input values. This controls if the OK button is enabled or not.
        # valueInput = inputs.itemById('value_input')
        # if valueInput.value >= 0:
        #     args.areInputsValid = True
        # else:
        #     args.areInputsValid = False
            
    # This event handler is called when the command terminates.
    @staticmethod
    def command_destroy(args: adsk.core.CommandEventArgs):
        # General logging for debug.
        Utils.log(f'{config.CMD_NAME} Command Destroy Event')

        PostDialog._local_handlers = []  # clear out the local handlers list

    @staticmethod
    def createDialog(command: adsk.core.Command):

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
        inputTab = inputs.addTabCommandInput(PostDialog._INPUT_SELECTION_TAB_ID, Strings("Input Selection"))
        inputTab.activate()

        #region Program dropdown
        input = inputTab.children.addDropDownCommandInput(PostDialog._PROGRAM_DROPDOWN_ID, Strings('NC Program'), DropDownStyles.TextListDropDownStyle)
        input.tooltip = Strings("TOOL TIP: NC Program to Use")
        input.tooltipDescription = Strings("TOOLTIP TEXT: NC Program to Use")
        for program in Programs:
            if not program.hasError and not program.isEmpty and not program.isSuppressed:
                input.listItems.add(program.programName, False)
        input.isEnabled = True
        #endregion

        #region Program machine text field
        input = inputTab.children.addStringValueInput(PostDialog._MACHINE_ID, Strings('Machine'), Strings('<Select program>'))
        input.tooltip = Strings("TOOL TIP: Machine")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Machine")
        input.isReadOnly = True
        input.isEnabled = False
        #endregion

        #region Post Processor text field
        input = inputTab.children.addStringValueInput(PostDialog._POST_PROCESSOR_ID, Strings('Post Processor'), Strings('<Select program>'))
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
                inputs.addBoolValueInput(f"setupSelected_{setup.name}", '', True, '', setup.isSelected),row,0)
            input.addCommandInput(
                init(inputs.addStringValueInput(f"setupName_{setup.name}", '', setup.name),
                    isReadOnly = True,
                    isEnabled = setup.isSelected
                ),row,1)
            input.addCommandInput(
                init(inputs.addStringValueInput(f"setupOrigin_{setup.name}", '', ''),
                    isReadOnly = True,
                    isEnabled = setup.isSelected
                ),row,2)
            input.addCommandInput(
                init(inputs.addStringValueInput(f"setupXNormal_{setup.name}", '', ''),
                    isReadOnly = True,
                    isEnabled = setup.isSelected
                ),row,3)
            input.addCommandInput(
                init(inputs.addStringValueInput(f"setupARotation_{setup.name}", '', ''),
                    isReadOnly = True,
                    isEnabled = setup.isSelected
                ),row,4)
        #endregion
        #endregion -----

        #region ----- [ G-code tab ] -----

        gCodeTab = inputs.addTabCommandInput(PostDialog._GCODE_OPTIONS_GROUP_ID, Strings("G-code options"))
        gCodeTab.isEnabled = False

        #region Tool change string input
        input = gCodeTab.children.addTextBoxCommandInput(PostDialog._TOOL_CHANGE_ID, Strings('Tool change code'), Settings(Settings.TOOL_CHANGE), 3, False)
        input.tooltip = Strings("TOOL TIP: Tool change code")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Tool change code")
        #endregion

        #region dummy input to separate the textboxes properly
        dummy = gCodeTab.children.addStringValueInput('dummy', '')
        dummy.isEnabled = False
        dummy.isReadOnly = True
        #endregion

        #region Body end codes textbox input
        input = gCodeTab.children.addTextBoxCommandInput(PostDialog._END_CODES_ID, Strings('G-codes that mark ending sequence'), Settings(Settings.END_CODES), 3, False)
        input.tooltip = Strings("TOOL TIP: G-codes that mark ending sequence")
        input.tooltipDescription = Strings("TOOLTIP TEXT: G-codes that mark ending sequence")

        dummy = gCodeTab.children.addBoolValueInput('','', True, "", False) # As the TextBoxCommandInput above seems to be buggy we add a dummy input to create some space
        dummy.isEnabled = False
        #endregion

        #region Header end codes textbox input
        input = gCodeTab.children.addTextBoxCommandInput(PostDialog._HEADER_CODES_ID, Strings('G-codes that mark header end'), Settings(Settings.HEADER_END_CODES), 3, False)
        input.tooltip = Strings("TOOL TIP: G-codes that mark header end")
        input.tooltipDescription = Strings("TOOLTIP TEXT: G-codes that mark header end")

        dummy = gCodeTab.children.addBoolValueInput('','', True, "", False) # As the TextBoxCommandInput above seems to be buggy we add a dummy input to create some space
        dummy.isEnabled = False
        #endregion

        #region Restore rapid moves checkbox
        input = gCodeTab.children.addBoolValueInput(PostDialog._RESTORE_RAPID_MOVES_ID,Strings('Restore rapid moves'), True, "", Settings(Settings.RESTORE_RAPID_MOVES))
        input.tooltip = Strings("TOOL TIP: Restore rapid moves")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Restore rapid moves")
        #endregion
        #endregion -----

        #region ----- [ Output tab ] -----
        outputTab = inputs.addTabCommandInput(PostDialog._OUTPUT_GROUP_ID, Strings("Output Options"))
        outputTab.isEnabled = False

        #region -- Output folder table --
        input = outputTab.children.addTableCommandInput(PostDialog._OUTPUT_FOLDER_TABLE_ID, Strings('Output folder'), 2, '12:1')
        input.minimumVisibleRows = 2
        input.maximumVisibleRows = 2
        input.tablePresentationStyle = adsk.core.TablePresentationStyles.transparentBackgroundTablePresentationStyle

        #region Output folder label, spans 2 columns
        input.addCommandInput(
            init(inputs.addStringValueInput(PostDialog._OUTPUT_FOLDER_LABEL_ID, '', Strings("Output folder")), 
                tooltip = Strings("TOOL TIP: Output folder"),
                tooltipDescription = Strings("TOOLTIP TEXT: Output folder"),
                isReadOnly = True
            ), 0, 0, 0, 2)
        #endregion

        #region Output folder string input
        input.addCommandInput(
            init(inputs.addStringValueInput(PostDialog._OUTPUT_FOLDER_ID, Strings("Output folder"), Strings("<Select program>")),
                tooltip = Strings("TOOL TIP: Output folder"),
                tooltipDescription = Strings("TOOLTIP TEXT: Output folder"),
                isReadOnly = False
            ), 1, 0)
        #endregion

        #region Output folder browse button
        input.addCommandInput(inputs.addBoolValueInput(PostDialog._OUTPUT_FOLDER_BUTTON_ID, '  …  ', False, '', False), 1, 1)
        #endregion
        #endregion

        #region File name string input
        input = outputTab.children.addStringValueInput(PostDialog._FILE_NAME_ID, Strings("File name"), Strings("<Select program>"))
        input.tooltip = Strings("TOOL TIP: File name")
        input.tooltipDescription = Strings("TOOLTIP TEXT: File name")
        #endregion

        #region Numeric name checkbox
        input = outputTab.children.addBoolValueInput(PostDialog._NUMERIC_NAME_ID, Strings("Name must be numeric"), True, "", Settings(Settings.NUMERIC_NAME))
        input.tooltip = Strings("TOOL TIP: Name must be numeric")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Name must be numeric")
        #endregion

        #region Prepend sequence number dropdown
        input = outputTab.children.addDropDownCommandInput(PostDialog._PREPEND_SEQUENCE_ID, Strings("Prepend sequence number"), adsk.core.DropDownStyles.TextListDropDownStyle)
        input.tooltip = Strings("TOOL TIP: Prepend sequence number")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Prepend sequence number")
        input.listItems.add(Strings("File names only"), input.listItems.count == Settings(Settings.SEQUENCE))
        input.listItems.add(Strings("Operation steps only"), input.listItems.count == Settings(Settings.SEQUENCE))
        input.listItems.add(Strings("File names and operation steps"), input.listItems.count == Settings(Settings.SEQUENCE))
        input.listItems.add(Strings("None"), input.listItems.count == Settings(Settings.SEQUENCE))
        #endregion

        #region Numbering digits spinner input
        input = outputTab.children.addIntegerSpinnerCommandInput(PostDialog._DIGITS_COUNT_ID, Strings("Numbering digits"), 1, 6, 1, Settings(Settings.NAME_DIGITS))
        input.tooltip = Strings("TOOL TIP: Numbering digits")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Numbering digits")
        #endregion

        #region Numbering interval spinner input
        input = outputTab.children.addIntegerSpinnerCommandInput(PostDialog._NUMBERING_INTERVAL_ID, Strings("Numbering interval"), 1, 6, 1, Settings(Settings.NUMBERING_INTERVAL))
        input.tooltip = Strings("TOOL TIP: Numbering interval")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Numbering interval")
        #endregion

        #region Combine tool checkbox
        input = outputTab.children.addBoolValueInput(PostDialog._COMBINE_TOOLS_ID, Strings('Combine operations using same tool'), True, "", Settings(Settings.COMBINE_TOOL))
        input.tooltip = Strings("TOOL TIP: Combine operations using same tool")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Combine operations using same tool")
        #endregion

        #region Rotate A-Axis between setups checkbox
        input = outputTab.children.addBoolValueInput(PostDialog._ROTATE_A_AXIS_ID, Strings('Rotate A-Axis between setups'), True, "", Settings(Settings.ROTATE_A_AXIS))
        input.tooltip = Strings("TOOL TIP: Rotate A-Axis between setups")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Rotate A-Axis between setups")
        #endregion

        #region Retract to safe Y on A-axis rotation checkbox
        input = outputTab.children.addBoolValueInput(PostDialog._SAFE_Y_RETRACTION_ID, Strings("Retract Y on A-axis rotation"), True, "", Settings(Settings.SAFE_Y_RETRACTION))
        input.tooltip = Strings("TOOL TIP: Retract Y on A-axis rotation")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Retract Y on A-axis rotation")
        #endregion

        #region Safe Y-retraction coordinate number
        input = outputTab.children.addIntegerSpinnerCommandInput(PostDialog._Y_RETRACTION_COORDINATE_ID, Strings("Safe Y-retraction coordinate (mm)"), -150, 0, 1, Settings(Settings.Y_RETRACTION_COORDINATE))
        input.tooltip = Strings("TOOL TIP: Safe Y-retraction coordinate (mm)")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Safe Y-retraction coordinate (mm)")
        #endregion

        #region Operations grouping dropdown
        input = outputTab.children.addDropDownCommandInput(PostDialog._OPERATIONS_GROUPING_ID, Strings("Operations grouping"), adsk.core.DropDownStyles.TextListDropDownStyle)
        input.tooltip = Strings("TOOL TIP: Operations grouping")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Operations grouping")
        # input.listItems.add(Strings("Single file"), input.listItems.count == Settings(Settings.OPERATIONS_GROUPING))
        # input.listItems.add(Strings("Group on setup"), input.listItems.count == Settings(Settings.OPERATIONS_GROUPING))
        # input.listItems.add(Strings("Group on setup and tool"), input.listItems.count == Settings(Settings.OPERATIONS_GROUPING))
        # input.listItems.add(Strings("None, one file per operation"), input.listItems.count == Settings(Settings.OPERATIONS_GROUPING))

        #endregion

        #region Flat file structure checkbox
        input = outputTab.children.addBoolValueInput(PostDialog._FLAT_FILE_STRUCTURE_ID, Strings("Flat file structure"), True, "", Settings(Settings.FLAT_FILE_STRUCTURE))
        input.tooltip = Strings("TOOL TIP: Flatten the file structure")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Flatten the file structure")
        #endregion

        #region Delete existing files checkbox
        input = outputTab.children.addBoolValueInput(PostDialog._DELETE_EXISTING_FILES_ID, Strings("Delete existing files"),  True, "", Settings(Settings.DEL_FILES))
        input.tooltip = Strings("TOOL TIP: Delete existing files")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Delete existing files")
        input.isEnabled = False
        #endregion

        #region Delete output folder checkbox
        input = outputTab.children.addBoolValueInput(PostDialog._DELETE_OUTPUT_FOLDER_ID, Strings("Delete output folder"),  True, "", Settings(Settings.DEL_FOLDER))
        input.tooltip = Strings("TOOL TIP: Delete output folder")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Delete output folder")
        #endregion -----
        #endregion

        #region ----- [ Misc tab ] -----
        miscTab = inputs.addTabCommandInput(PostDialog._RENAME_SETUPS_GROUP_ID, Strings("Misc"))

        #region ----- [ Rename setups group ] -----
        group = miscTab.children.addGroupCommandInput(PostDialog._RENAME_SETUPS_GROUP_ID, Strings("Rename Setups"))
        group.isExpanded = True

        #region Use regex checkbox
        input = group.children.addBoolValueInput(PostDialog._USE_REGEX_ID, Strings("Use Python regular expressions"), True, "", Settings(Settings.USE_REGEX))
        input.tooltip = Strings("TOOL TIP: Use Python regular expressions")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Use Python regular expressions")
        #endregion

        #region Find string input
        input = group.children.addStringValueInput(PostDialog._FIND_STRING_ID, Strings("Search for this string"), Settings(Settings.FIND_STRING))
        input.tooltip = Strings("TOOL TIP: Search for this string")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Search for this string")
        #endregion

        #region Replace string input
        input = group.children.addStringValueInput(PostDialog._REPLACE_STRING_ID, Strings("Replace with this string"), Settings(Settings.REPLACE_STRING))
        input.tooltip = Strings("TOOL TIP: Replace with this string")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Replace with this string")
        #endregion

        #region Replace button
        input = group.children.addBoolValueInput(PostDialog._REPLACE_ID, f"   {Strings("Search and replace")}   ", False)
        input.isFullWidth = True
        input.tooltip = Strings("TOOL TIP: Search and replace")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Search and replace")
        #endregion
        #endregion -----

        #region ----- [ Advanced settings ] -----
        group = miscTab.children.addGroupCommandInput(PostDialog._ADVANCED_SETTINGS_GROUP_ID, Strings("Advanced Settings"))
        group.isExpanded = True

        #region Initial delay spinner input
        input = group.children.addFloatSpinnerCommandInput(PostDialog._INITIAL_DELAY_ID, Strings("Initial time allowance"), "s", 0.1, 1.0, 0.1, Settings(Settings.INITIAL_DELAY))
        input.tooltip = Strings("TOOL TIP: Initial time allowance")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Initial time allowance")
        #endregion

        #region Post retries spinner input
        input = group.children.addIntegerSpinnerCommandInput(PostDialog._POST_RETRIES_ID, Strings("Number of retries"), 1, 9, 1, Settings(Settings.POST_RETRIES))
        input.tooltip = Strings("TOOL TIP: Number of retries")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Number of retries")
        #endregion
        #endregion -----
        #endregion

        #region Save as default button
        input = inputs.addSeparatorCommandInput('dummy')

        input = inputs.addBoolValueInput(PostDialog._SAVE_ID, f"   {Strings("Save as default settings")}   ", False)
        input.tooltip = Strings("TOOL TIP: Save as default settings")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Save as default settings")
        input.isFullWidth = True
        input.isEnabled = False
        #endregion

        #endregion ----------------------------------------------------

        #region Hook up events
        Events.add(command.execute, PostDialog.command_execute, local_handlers=PostDialog._local_handlers)
        Events.add(command.mouseDown, PostDialog.commandMouseDown, local_handlers=PostDialog._local_handlers)
        Events.add(command.mouseUp, PostDialog.commandMouseUp, local_handlers=PostDialog._local_handlers)
        Events.add(command.inputChanged, PostDialog.commandInputChanged, local_handlers=PostDialog._local_handlers)
        # Events.add(command.executePreview, PostProcessorDialog.command_preview, local_handlers=PostProcessorDialog._local_handlers)
        Events.add(command.validateInputs, PostDialog.command_validate_input, local_handlers=PostDialog._local_handlers)
        Events.add(command.destroy, PostDialog.command_destroy, local_handlers=PostDialog._local_handlers)
        #endregion

        # Finally, update the dialog based on current choices and settings
        PostDialog._updateDialog(command)

    mouseDown = False
    @classmethod
    def commandMouseDown(cls, args: adsk.core.MouseEventArgs):
        PostDialog.mouseDown = True
        Utils.log(f'{config.CMD_NAME} Mouse Down Event')

    @classmethod
    def commandMouseUp(cls, args: adsk.core.MouseEventArgs):
        PostDialog.mouseDown = False
        Utils.log(f'{config.CMD_NAME} Mouse Down Up')

    @classmethod
    def _updateOperationsGroupingDropdown(cls, command):
        inputs = command.commandInputs
        rotateAAxisCheckbox: adsk.core.BoolValueCommandInput = inputs.itemById(PostDialog._ROTATE_A_AXIS_ID)

        _, badOrigins, _ = Setups.getWCSAlignmentIssues()

        operationsGroupingDropdown = inputs.itemById(PostDialog._OPERATIONS_GROUPING_ID)
        # Since it isn't possible to hide list items, let's recreate 
        # the list.
        # Only issue is that list items doesn't have an Id, so we need 
        # to rely on the text to identify them. Which is translateable,
        # so that's why the dictionary and all the other shenanigans.
        operationsGroupingsTexts = {
            Settings.OperationsGroupings.SINGLE_FILE: Strings("Single file"),
            Settings.OperationsGroupings.SETUP: Strings("Group on setup"),
            Settings.OperationsGroupings.SETUP_AND_TOOL: Strings("Group on setup and tool"),
            Settings.OperationsGroupings.PER_OPERATION: Strings("None, one file per operation")
        }
        operationsGroupingDropdown.listItems.clear()
        for key in operationsGroupingsTexts:
            addItem = True
            if key == Settings.OperationsGroupings.SINGLE_FILE:
                addItem = Programs.Current is not None \
                    and len(badOrigins) == 0 \
                    and Programs.Current.machineHasAAxis \
                    and rotateAAxisCheckbox.value
            if addItem:
                operationsGroupingDropdown.listItems.add(operationsGroupingsTexts[key], False)
        
        selectedText = operationsGroupingsTexts.get(Settings(Settings.OPERATIONS_GROUPING))
        itemFound = False
        groupOnSetup = None
        for i in range(operationsGroupingDropdown.listItems.count):
            item = operationsGroupingDropdown.listItems.item(i)
            if item.name == operationsGroupingsTexts.get(Settings.OperationsGroupings.SETUP):
                groupOnSetup = item
            if item.name == selectedText:
                item.isSelected = True
                itemFound = True
                break
        if not itemFound and groupOnSetup is not None:
            groupOnSetup.isSelected = True

    @classmethod
    def _updateSetupsTable(cls, command):
        inputs = command.commandInputs
        rotateAAxisCheckbox: adsk.core.BoolValueCommandInput = inputs.itemById(PostDialog._ROTATE_A_AXIS_ID)
        rotateAAxisCheckbox.isEnabled = False if Programs.Current is None else Programs.Current.machineHasAAxis

        firstSetup: Setup = None
        for setup in Setups:
            isSelected = setup.isSelected

            inputName = inputs.itemById(f"setupName_{setup.name}")
            origin = inputs.itemById(f"setupOrigin_{setup.name}")
            xNormalInput = inputs.itemById(f"setupXNormal_{setup.name}")
            aRotation = inputs.itemById(f"setupARotation_{setup.name}")
            
            inputName.isEnabled = isSelected
            origin.isEnabled = isSelected
            xNormalInput.isEnabled = isSelected
            aRotation.isEnabled = isSelected

            if firstSetup is None:
                if isSelected:
                    firstSetup = setup
                origin.value = Strings("(reference)") if isSelected else '-'
                xNormalInput.value = Strings("(reference)") if isSelected else '-'
                aRotation.value = Strings("(reference)") if isSelected else '-'
                continue

            equalOrigin = setup.origin.isEqualTo(firstSetup.origin)
            parallelXAxis = setup.xNormal.isParallelTo(firstSetup.xNormal)

            origin.value = '' if firstSetup is None else \
                Strings("Same") if equalOrigin else Strings("Different")
            xNormalInput.value = '' if firstSetup is None else \
                Strings("Aligned") if parallelXAxis else Strings("Misaligned") 
            aRotation.value = '' if firstSetup is None or not parallelXAxis else \
                f"{round(setup.GetRotationAroundXAxisRelativeToDeg(firstSetup)*1000)/1000}°"

    @classmethod
    def _updateFlatFileStructure(cls, command):
        inputs = command.commandInputs
        operationsGroupingDropdown: adsk.core.DropDownCommandInput = inputs.itemById(PostDialog._OPERATIONS_GROUPING_ID)
        flatFileStructureCheckbox: adsk.core.BoolValueCommandInput = inputs.itemById(PostDialog._FLAT_FILE_STRUCTURE_ID)

        # Disable flat file structure if operations grouping is single file
        flatFileStructureCheckbox.isEnabled = operationsGroupingDropdown.selectedItem is not None and operationsGroupingDropdown.selectedItem.name != Strings("Single file") 
    
    @classmethod
    def _updateYRetractionCoordinate(cls, command):
        inputs = command.commandInputs
        rotateAAxisCheckbox: adsk.core.BoolValueCommandInput = inputs.itemById(PostDialog._ROTATE_A_AXIS_ID)
        safeYRetractionCheckbox: adsk.core.BoolValueCommandInput = inputs.itemById(PostDialog._SAFE_Y_RETRACTION_ID)
        yRetractionCoordinateSpinner: adsk.core.IntegerSpinnerCommandInput = inputs.itemById(PostDialog._Y_RETRACTION_COORDINATE_ID)

        yRetractionCoordinateSpinner.isEnabled = Programs.Current is not None and Programs.Current.machineHasAAxis and rotateAAxisCheckbox.value and safeYRetractionCheckbox.value

    @classmethod
    def _updateSafeYRetraction(cls, command):
        inputs = command.commandInputs
        rotateAAxisCheckbox: adsk.core.BoolValueCommandInput = inputs.itemById(PostDialog._ROTATE_A_AXIS_ID)
        safeYRetractionCheckbox: adsk.core.BoolValueCommandInput = inputs.itemById(PostDialog._SAFE_Y_RETRACTION_ID)

        safeYRetractionCheckbox.isEnabled = Programs.Current is not None and Programs.Current.machineHasAAxis and rotateAAxisCheckbox.value

    @classmethod
    def _updateDialog(cls, command):
        PostDialog._updateOperationsGroupingDropdown(command)
        PostDialog._updateSetupsTable(command)
        PostDialog._updateFlatFileStructure(command)
        PostDialog._updateYRetractionCoordinate(command)
        PostDialog._updateSafeYRetraction(command)

    #region on...Changed handlers
    @staticmethod
    def onProgramChanged(dropdown: adsk.core.DropDownCommandInput):

        inputs = dropdown.parentCommand.commandInputs

        selectedItem = dropdown.selectedItem
        if selectedItem:
            programName = selectedItem.name
            program = next((prog for prog in Programs if prog.programName == programName), None)
            if program:
                if(program.hasError):
                    return

                if Programs.Current is not None:
                    Settings.Save(Programs.Current.attributes)

                Programs.Current = program
                Utils.log(f'Selected NC program: {program.programName}')

                Settings.Load(Programs.Current.attributes)

                if Programs.Current.hasWarning:
                    app = adsk.core.Application.get()
                    ui = app.userInterface
                    ui.messageBox(Strings("The selected NC Program has the following warning:\n{warning}").format(warning = Programs.Current.warning),
                                                    Const.CMD_NAME,
                                                    adsk.core.MessageBoxButtonTypes.OKButtonType)

                inputs = inputs.command.commandInputs
                # Input Selection tab
                inputs.itemById(PostDialog._MACHINE_ID).isEnabled = True
                inputs.itemById(PostDialog._POST_PROCESSOR_ID).isEnabled = True

                inputs.itemById(PostDialog._GCODE_OPTIONS_GROUP_ID).isEnabled = True
                inputs.itemById(PostDialog._OUTPUT_GROUP_ID).isEnabled = True

                inputs.itemById(PostDialog._SAVE_ID).isEnabled = True

                outputPathText: adsk.core.StringValueCommandInput = inputs.itemById(PostDialog._OUTPUT_FOLDER_ID)
                outputPathText.value = Programs.Current.Parameters.Get(Parameters.OUTPUT_FOLDER)

                machineText: adsk.core.StringValueCommandInput = inputs.itemById(PostDialog._MACHINE_ID)
                machineText.value = Programs.Current.machineName

                postProcessorText: adsk.core.StringValueCommandInput = inputs.itemById(PostDialog._POST_PROCESSOR_ID)
                postProcessorText.value = Programs.Current.postProcessorDescription

                fileNameText: adsk.core.StringValueCommandInput = inputs.itemById(PostDialog._FILE_NAME_ID)
                fileNameText.value = Programs.Current.fileName

                PostDialog._updateDialog(dropdown.parentCommand)

    @staticmethod
    def onRotateAAxisChanged(checkbox: adsk.core.BoolValueCommandInput):
        Settings.Set(Settings.ROTATE_A_AXIS, checkbox.value)
            
        if(checkbox.value):
            app = adsk.core.Application.get()
            ui = app.userInterface
    
            allAligned, badOrigins, badXAxes = Setups.getWCSAlignmentIssues()

            if not allAligned:
                msg = "<i><u>Warning:</u></i> Using 4th axis rotation while all Work Coordinate Systems isn't aligned properly may result in unexpected results, including damage to property and person."
                msg += "<p>Do NOT use the result from this plug-in unless you have personally verified that the result can be used.<p>" 
                # TODO: Add list of bad WCS setups
                ui.messageBox(msg,
                "WARNING! Do not proceed!", 
                adsk.core.MessageBoxButtonTypes.OKButtonType,
                adsk.core.MessageBoxIconTypes.WarningIconType)
            

        command = checkbox.parentCommand
        PostDialog._updateOperationsGroupingDropdown(command)
        PostDialog._updateSafeYRetraction(command)
        PostDialog._updateYRetractionCoordinate(command)
        
        inputs = command.commandInputs
        safeYRetractionCheckbox: adsk.core.BoolValueCommandInput = inputs.itemById(PostDialog._SAFE_Y_RETRACTION_ID)
        safeYRetractionCheckbox.isEnabled = checkbox.value

    @staticmethod
    def onPrependSequenceChanged(dropdown: adsk.core.CommandInput):
        Settings.Set(Settings.SEQUENCE, dropdown.selectedItem.index)

        inputs = dropdown.parentCommand.commandInputs
        digitsInput: adsk.core.IntegerSpinnerCommandInput = inputs.itemById(PostDialog._DIGITS_COUNT_ID)
        Settings.Set(Settings.SEQUENCE, dropdown.selectedItem.index)
        if dropdown.selectedItem.name == Strings("None"):
            digitsInput.isEnabled = False
        else:
            digitsInput.isEnabled = True

    @staticmethod
    def onRestoreRapidMovesChanged(checkbox: adsk.core.BoolValueCommandInput):
        Settings.Set(Settings.RESTORE_RAPID_MOVES, checkbox.value)

    @staticmethod
    def onToolChangeChanged(textbox: adsk.core.TextBoxCommandInput):
        Settings.Set(Settings.TOOL_CHANGE, textbox.text)

    @staticmethod
    def onEndCodesChanged(textbox: adsk.core.TextBoxCommandInput):
        Settings.Set(Settings.END_CODES, textbox.text)

    @staticmethod
    def onOutputFolderChanged(input: adsk.core.StringValueCommandInput):
        newFolder = Path(input.value.strip())
        if newFolder != Programs.Current.GetOutputFolder():
            Programs.Current.SetOutputFolder(newFolder)

    @staticmethod
    def onOutputFolderButtonChanged(button: adsk.core.BoolValueCommandInput):
        inputs = button.parentCommand.commandInputs
        app: adsk.core.Application = adsk.core.Application.get()
        ui = app.userInterface
        dialog = ui.createFolderDialog()
        dialog.initialDirectory = inputs.itemById(PostDialog._OUTPUT_FOLDER_ID).value
        dialog.title = Strings("Select Output Folder")
        if dialog.showDialog() != adsk.core.DialogResults.DialogOK:
            return
        folder = dialog.folder
        if folder:
            Programs.Current.SetOutputFolder(folder)
            outputFolderInput: adsk.core.StringValueCommandInput = inputs.itemById(PostDialog._OUTPUT_FOLDER_ID)
            outputFolderInput.value = folder

    @staticmethod
    def onNumericNameChanged(checkbox: adsk.core.BoolValueCommandInput):
        Settings.Set(Settings.NUMERIC_NAME, checkbox.value)

    @staticmethod
    def onDigitsCountChanged(spinner: adsk.core.IntegerSpinnerCommandInput):
        Settings.Set(Settings.NAME_DIGITS, spinner.value)

    @staticmethod
    def onCombineToolsChanged(checkbox: adsk.core.BoolValueCommandInput):
        Settings.Set(Settings.COMBINE_TOOL, checkbox.value)

    @staticmethod
    def onSafeYRetractionChanged(checkbox: adsk.core.BoolValueCommandInput):
        Settings.Set(Settings.SAFE_Y_RETRACTION, checkbox.value)
        PostDialog._updateYRetractionCoordinate(checkbox.parentCommand)

    @staticmethod
    def onYRetractionCoordinateChanged(spinner: adsk.core.IntegerSpinnerCommandInput):
        Settings.Set(Settings.Y_RETRACTION_COORDINATE, spinner.value)

    @staticmethod
    def onOperationsGroupingChanged(dropdown: adsk.core.DropDownCommandInput):
        Settings.Set(Settings.OPERATIONS_GROUPING, dropdown.selectedItem.index)
        PostDialog._updateFlatFileStructure(dropdown.parentCommand)

    @staticmethod
    def onFlatFileStructureChanged(checkbox: adsk.core.BoolValueCommandInput):
        Settings.Set(Settings.FLAT_FILE_STRUCTURE, checkbox.value)

    @staticmethod
    def onDeleteExistingFilesChanged(checkbox: adsk.core.BoolValueCommandInput):
        Settings.Set(Settings.DEL_FILES, checkbox.value)
    
    @staticmethod
    def onDeleteOutputFolderChanged(checkbox: adsk.core.BoolValueCommandInput):
        Settings.Set(Settings.DEL_FOLDER, checkbox.value)

    @staticmethod
    def onUseRegexChanged(checkbox: adsk.core.BoolValueCommandInput):
        Settings.Set(Settings.USE_REGEX, checkbox.value)
    
    @staticmethod
    def onFindStringChanged(input: adsk.core.StringValueCommandInput):
        Settings.Set(Settings.FIND_STRING, input.value)

    @staticmethod
    def onReplaceStringChanged(input: adsk.core.StringValueCommandInput):
        Settings.Set(Settings.REPLACE_STRING, input.value)

    @staticmethod
    def onReplaceChanged(checkbox: adsk.core.BoolValueCommandInput):
        Settings.Set(Settings.REPLACE, checkbox.value)

    @staticmethod
    def onInitialDelayChanged(spinner: adsk.core.FloatSpinnerCommandInput):
        Settings.Set(Settings.INITIAL_DELAY, spinner.value)

    @staticmethod
    def onPostRetriesChanged(spinner: adsk.core.IntegerSpinnerCommandInput):
        Settings.Set(Settings.POST_RETRIES, spinner.value)

    @staticmethod
    def onFileNameChanged(input: adsk.core.StringValueCommandInput):
        Programs.Current.SetFileName(input.value)

    @staticmethod
    def onSaveChanged(checkbox: adsk.core.BoolValueCommandInput):
        pass # TODO: Implement saving default settings
    
    @staticmethod
    def onSetupSelectedChanged(checkbox: adsk.core.BoolValueCommandInput):
        setupName = checkbox.id.replace("setupSelected_", "")
        setup = next((s for s in Setups if s.name == setupName), None)
        if setup and setup.isSelected != checkbox.value:
            Utils.log(f'Updating setup selection from dialog: {setup.name} selected={checkbox.value}')
            setup.select(checkbox.value)
            PostDialog._updateDialog(checkbox.parentCommand)
    #endregion