from pathlib import Path
import adsk

from ....lib.fusionAddInUtils.general_utils import Utils
from .. import config

from ..parameters import Parameters
from ..programs import Programs
from ..setups.setups import Setups
from ..setups.setup import Setup
from ..const import Const
from ..settings import Settings
from ..strings import Strings

class PostDialogOnEvent:

    # This event handler is called when the user changes anything in the command dialog
    # allowing you to modify values of other inputs based on that change.
    # They are all split down to their separate onEvent handler for better
    # readability and maintainability.
    @classmethod
    def commandInputChanged(cls, args: adsk.core.InputChangedEventArgs):
        changedInput = args.input

        if changedInput.id == cls._PROGRAM_DROPDOWN_ID:
            cls.onProgramChanged(changedInput)
        
        elif changedInput.id == cls._TOOL_CHANGE_ID:
            cls.onToolChangeChanged(changedInput)

        elif changedInput.id == cls._END_CODES_ID:
            cls.onEndCodesChanged(changedInput)

        elif changedInput.id == cls._RESTORE_RAPID_MOVES_ID:
            cls.onRestoreRapidMovesChanged(changedInput)

        elif changedInput.id == cls._OUTPUT_FOLDER_ID:
            cls.onOutputFolderChanged(changedInput)
        
        elif changedInput.id == cls._OUTPUT_FOLDER_BUTTON_ID:
            cls.onOutputFolderButtonChanged(changedInput)

        elif changedInput.id == cls._NUMERIC_NAME_ID:
            cls.onNumericNameChanged(changedInput)

        elif changedInput.id == cls._PREPEND_SEQUENCE_ID:
            cls.onPrependSequenceChanged(changedInput)
            
        elif changedInput.id == cls._DIGITS_COUNT_ID:
            cls.onDigitsCountChanged(changedInput)
        
        elif changedInput.id == cls._COMBINE_TOOLS_ID:
            cls.onCombineToolsChanged(changedInput)

        elif changedInput.id == cls._ROTATE_A_AXIS_ID:
            cls.onRotateAAxisChanged(changedInput)

        elif changedInput.id == cls._SAFE_Y_RETRACTION_ID:
            cls.onSafeYRetractionChanged(changedInput)

        elif changedInput.id == cls._Y_RETRACTION_COORDINATE_ID:
            cls.onYRetractionCoordinateChanged(changedInput)

        elif changedInput.id == cls._OPERATIONS_GROUPING_ID:
            cls.onOperationsGroupingChanged(changedInput)

        elif changedInput.id == cls._FLAT_FILE_STRUCTURE_ID:
            cls.onFlatFileStructureChanged(changedInput)

        elif changedInput.id == cls._DELETE_EXISTING_FILES_ID:
            cls.onDeleteExistingFilesChanged(changedInput)

        elif changedInput.id == cls._DELETE_OUTPUT_FOLDER_ID:
            cls.onDeleteOutputFolderChanged(changedInput)

        elif changedInput.id == cls._USE_REGEX_ID:
            cls.onUseRegexChanged(changedInput)

        elif changedInput.id == cls._FIND_STRING_ID:
            cls.onFindStringChanged(changedInput)

        elif changedInput.id == cls._REPLACE_STRING_ID:
            cls.onReplaceStringChanged(changedInput)

        elif changedInput.id == cls._REPLACE_ID:
            cls.onReplaceChanged(changedInput)

        elif changedInput.id == cls._INITIAL_DELAY_ID:
            cls.onInitialDelayChanged(changedInput)

        elif changedInput.id == cls._POST_RETRIES_ID:
            cls.onPostRetriesChanged(changedInput)
        
        elif changedInput.id == cls._SAVE_ID:
            cls.onSaveChanged(changedInput)

        elif changedInput.id == cls._FILE_NAME_ID:
            cls.onFileNameChanged(changedInput)

        elif changedInput.id == cls._HEADER_CODES_ID:
            cls.onHeaderCodesChanged(changedInput)

        elif changedInput.id == cls._SELECT_ALL_SETUPS_ID:
            cls.onSelectAllSetupsChanged(changedInput)

        elif changedInput.id.startswith('setupSelected_'):
            cls.onSetupSelectedChanged(changedInput)
        
        # General logging for debug.
        Utils.log(f'{config.CMD_NAME} Input Changed Event fired from a change to {changedInput.id}')

    @classmethod
    def _updateDialog(cls, command: adsk.core.Command):
        """Updates all the controls of the dialog based on the current 
        settings and selected program. This is called after changing 
        the selected program and after loading settings to update the 
        dialog to reflect those changes."""

        cls._updateOperationsGroupingDropdown(command)
        cls._updateSetupsTable(command)
        cls._updateFlatFileStructure(command)
        cls._updateYRetractionCoordinate(command)
        cls._updateSafeYRetraction(command)
        cls._updateTabs(command)


    @classmethod
    def _updateOperationsGroupingDropdown(cls, command: adsk.core.Command):
        inputs = command.commandInputs
        rotateAAxisCheckbox: adsk.core.BoolValueCommandInput = inputs.itemById(cls._ROTATE_A_AXIS_ID)

        _, badOrigins, _ = Setups.getWCSAlignmentIssues()

        operationsGroupingDropdown = inputs.itemById(cls._OPERATIONS_GROUPING_ID)
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
    def _updateSetupsTable(cls, command: adsk.core.Command):
        """Updates the setups table in the dialog, enabling/disabling 
        rows and setting values based on the selected program and 
        settings."""
        inputs = command.commandInputs
        rotateAAxisCheckbox: adsk.core.BoolValueCommandInput = inputs.itemById(cls._ROTATE_A_AXIS_ID)
        rotateAAxisCheckbox.isEnabled = False if Programs.Current is None else Programs.Current.machineHasAAxis

        firstSetup: Setup = None
        for setup in Setups:

            inputCheckbox: adsk.core.BoolValueCommandInput = inputs.itemById(f"setupSelected_{setup.index}")
            inputName: adsk.core.TextBoxCommandInput = inputs.itemById(f"setupName_{setup.index}")
            origin: adsk.core.TextBoxCommandInput = inputs.itemById(f"setupOrigin_{setup.index}")
            xNormalInput: adsk.core.TextBoxCommandInput = inputs.itemById(f"setupXNormal_{setup.index}")
            aRotation: adsk.core.TextBoxCommandInput = inputs.itemById(f"setupARotation_{setup.index}")

            inputCheckbox.value = setup.isSelected

            requiredRotation = 0

            if firstSetup is None:
                inputCheckbox.isEnabled = True
            else:
                requiredRotation = round(setup.GetRotationAroundXAxisRelativeToDeg(firstSetup), 3)

                equalOrigin = setup.origin.isEqualTo(firstSetup.origin)
                parallelXAxis = setup.xNormal.isParallelTo(firstSetup.xNormal)
                inputCheckbox.isEnabled = equalOrigin \
                    and parallelXAxis \
                    and Programs.Current.hasMachine \
                    and (Programs.Current.machineHasAAxis \
                         and (rotateAAxisCheckbox.value \
                              or requiredRotation == 0))
                if not inputCheckbox.isEnabled:
                    inputCheckbox.value = False
                    setup.select(False)

            inputName.isEnabled = setup.isSelected
            origin.isEnabled = setup.isSelected
            xNormalInput.isEnabled = setup.isSelected
            aRotation.isEnabled = setup.isSelected


            if firstSetup is None:
                if setup.isSelected:
                    firstSetup = setup
                    origin.value = xNormalInput.value = aRotation.value = Strings("(reference)")
                else:
                    origin.value = xNormalInput.value = aRotation.value = '-'
                continue

            origin.value = '' if firstSetup is None else \
                Strings("Same") if equalOrigin else Strings("Different")
            xNormalInput.value = '' if firstSetup is None else \
                Strings("Aligned") if parallelXAxis else Strings("Misaligned") 
            aRotation.value = '' if firstSetup is None or not parallelXAxis else \
                f"{requiredRotation}°"

    @classmethod
    def _updateFlatFileStructure(cls, command: adsk.core.Command):
        inputs = command.commandInputs
        operationsGroupingDropdown: adsk.core.DropDownCommandInput = inputs.itemById(cls._OPERATIONS_GROUPING_ID)
        flatFileStructureCheckbox: adsk.core.BoolValueCommandInput = inputs.itemById(cls._FLAT_FILE_STRUCTURE_ID)

        # Disable flat file structure if operations grouping is single file
        flatFileStructureCheckbox.isEnabled = operationsGroupingDropdown.selectedItem is not None and operationsGroupingDropdown.selectedItem.name != Strings("Single file") 
    
    @classmethod
    def _updateYRetractionCoordinate(cls, command: adsk.core.Command):
        inputs = command.commandInputs
        rotateAAxisCheckbox: adsk.core.BoolValueCommandInput = inputs.itemById(cls._ROTATE_A_AXIS_ID)
        safeYRetractionCheckbox: adsk.core.BoolValueCommandInput = inputs.itemById(cls._SAFE_Y_RETRACTION_ID)
        yRetractionCoordinateSpinner: adsk.core.IntegerSpinnerCommandInput = inputs.itemById(cls._Y_RETRACTION_COORDINATE_ID)

        yRetractionCoordinateSpinner.isEnabled = Programs.Current is not None and Programs.Current.machineHasAAxis and rotateAAxisCheckbox.value and safeYRetractionCheckbox.value

    @classmethod
    def _updateSafeYRetraction(cls, command: adsk.core.Command):
        inputs = command.commandInputs
        rotateAAxisCheckbox: adsk.core.BoolValueCommandInput = inputs.itemById(cls._ROTATE_A_AXIS_ID)
        safeYRetractionCheckbox: adsk.core.BoolValueCommandInput = inputs.itemById(cls._SAFE_Y_RETRACTION_ID)

        safeYRetractionCheckbox.isEnabled = Programs.Current is not None and Programs.Current.machineHasAAxis and rotateAAxisCheckbox.value

    @classmethod
    def _updateInputTab(cls, command: adsk.core.Command):
        inputs = command.commandInputs

        if Programs.Current is None:
            return

        machineText: adsk.core.StringValueCommandInput = inputs.itemById(cls._MACHINE_ID)
        machineText.isEnabled = True
        machineText.value = Programs.Current.machineName

        postProcessorText: adsk.core.StringValueCommandInput = inputs.itemById(cls._POST_PROCESSOR_ID)
        postProcessorText.isEnabled = True
        postProcessorText.value = Programs.Current.postProcessorDescription

    @classmethod
    def _updateTabs(cls, command: adsk.core.Command):
        inputs = command.commandInputs

        if Programs.Current is None:
            return

        cls._updateInputTab(command)

        inputs.itemById(cls._GCODE_OPTIONS_GROUP_ID).isEnabled = True
        inputs.itemById(cls._OUTPUT_GROUP_ID).isEnabled = True

        inputs.itemById(cls._SAVE_ID).isEnabled = True

        outputPathText: adsk.core.StringValueCommandInput = inputs.itemById(cls._OUTPUT_FOLDER_ID)
        outputPathText.value = Programs.Current.Parameters.Get(Parameters.OUTPUT_FOLDER)

        fileNameText: adsk.core.StringValueCommandInput = inputs.itemById(cls._FILE_NAME_ID)
        fileNameText.value = Programs.Current.fileName

    #region on...Changed handlers
    @classmethod
    def onProgramChanged(cls, dropdown: adsk.core.DropDownCommandInput):

        command = dropdown.parentCommand
        inputs = command.commandInputs

        selectedItem = dropdown.selectedItem
        if selectedItem:
            program = next((prog for prog in Programs if prog.name == selectedItem.name), None)
            if program:
                if(program.hasError):
                    return

                # Save settings of the previously selected program before switching to the new one
                if Programs.Current is not None:
                    Settings.Save(Programs.Current.attributes)

                Programs.Current = program
                Utils.log(f'Selected NC program: {program.name}')

                Settings.Load(Programs.Current.attributes)

                if Programs.Current.hasWarning:
                    app = adsk.core.Application.get()
                    ui = app.userInterface
                    ui.messageBox(Strings("The selected NC Program has the following warning:\n{warning}").format(warning = Programs.Current.warning),
                                                    Const.CMD_NAME,
                                                    adsk.core.MessageBoxButtonTypes.OKButtonType)


                Settings(Settings.NC_PROGRAM, program.name)

                cls._updateDialog(command)

    @classmethod
    def onRotateAAxisChanged(cls, checkbox: adsk.core.BoolValueCommandInput):
        Settings(Settings.ROTATE_A_AXIS, checkbox.value)

        app = adsk.core.Application.get()
        ui = app.userInterface
        command = checkbox.parentCommand

        if checkbox.value:
    
            allAligned, badOrigins, badXAxes = Setups.getWCSAlignmentIssues()

            if not allAligned:
                msg = "<i><u>Notice:</u></i> Some setups has been deselected as they have incompatible WCS origin/X-axis alignment."
                ui.messageBox(msg,
                "Incorrect WCS Alignment", 
                adsk.core.MessageBoxButtonTypes.OKButtonType,
                adsk.core.MessageBoxIconTypes.InformationIconType)
                cls._updateSetupsTable(command)
        else:
            requiresRotation, setupRotations = Setups.AAxisRotationRequired()            
            if requiresRotation:
                msg = "<i><u>Notice:</u></i> Some setups has been deselected as they require A-axis rotation."
                ui.messageBox(msg,
                "AAxis Rotation Disabled", 
                adsk.core.MessageBoxButtonTypes.OKButtonType,
                adsk.core.MessageBoxIconTypes.InformationIconType)
                cls._updateSetupsTable(command)

        command = checkbox.parentCommand
        cls._updateOperationsGroupingDropdown(command)
        cls._updateSafeYRetraction(command)
        cls._updateYRetractionCoordinate(command)
        
        inputs = command.commandInputs
        safeYRetractionCheckbox: adsk.core.BoolValueCommandInput = inputs.itemById(cls._SAFE_Y_RETRACTION_ID)
        safeYRetractionCheckbox.isEnabled = checkbox.value

    @classmethod
    def onPrependSequenceChanged(cls, dropdown: adsk.core.CommandInput):
        Settings(Settings.SEQUENCE, dropdown.selectedItem.index)

        inputs = dropdown.parentCommand.commandInputs
        digitsInput: adsk.core.IntegerSpinnerCommandInput = inputs.itemById(cls._DIGITS_COUNT_ID)
        Settings(Settings.SEQUENCE, dropdown.selectedItem.index)
        if dropdown.selectedItem.name == Strings("None"):
            digitsInput.isEnabled = False
        else:
            digitsInput.isEnabled = True

    @classmethod
    def onRestoreRapidMovesChanged(cls, checkbox: adsk.core.BoolValueCommandInput):
        Settings(Settings.RESTORE_RAPID_MOVES, checkbox.value)

    @classmethod
    def onToolChangeChanged(cls, textbox: adsk.core.TextBoxCommandInput):
        Settings(Settings.TOOL_CHANGE, textbox.text)

    @classmethod
    def onEndCodesChanged(cls, textbox: adsk.core.TextBoxCommandInput):
        Settings(Settings.END_CODES, textbox.text)

    @classmethod
    def onOutputFolderChanged(input: adsk.core.StringValueCommandInput):
        newFolder = Path(input.value.strip())
        if newFolder != Programs.Current.GetOutputFolder():
            Programs.Current.SetOutputFolder(newFolder)

    @classmethod
    def onOutputFolderButtonChanged(cls, button: adsk.core.BoolValueCommandInput):
        inputs = button.parentCommand.commandInputs
        app: adsk.core.Application = adsk.core.Application.get()
        ui = app.userInterface
        dialog = ui.createFolderDialog()
        dialog.initialDirectory = inputs.itemById(cls._OUTPUT_FOLDER_ID).value
        dialog.title = Strings("Select Output Folder")
        if dialog.showDialog() != adsk.core.DialogResults.DialogOK:
            return
        folder = dialog.folder
        if folder:
            Programs.Current.SetOutputFolder(Path(folder))
            outputFolderInput: adsk.core.StringValueCommandInput = inputs.itemById(cls._OUTPUT_FOLDER_ID)
            outputFolderInput.value = folder

    @classmethod
    def onNumericNameChanged(cls, checkbox: adsk.core.BoolValueCommandInput):
        Settings(Settings.NUMERIC_NAME, checkbox.value)

    @classmethod
    def onDigitsCountChanged(cls,spinner: adsk.core.IntegerSpinnerCommandInput):
        Settings(Settings.NAME_DIGITS, spinner.value)

    @classmethod
    def onCombineToolsChanged(cls, checkbox: adsk.core.BoolValueCommandInput):
        Settings(Settings.COMBINE_TOOL, checkbox.value)

    @classmethod
    def onSafeYRetractionChanged(cls,checkbox: adsk.core.BoolValueCommandInput):
        Settings(Settings.SAFE_Y_RETRACTION, checkbox.value)
        cls._updateYRetractionCoordinate(checkbox.parentCommand)

    @classmethod
    def onYRetractionCoordinateChanged(cls, spinner: adsk.core.IntegerSpinnerCommandInput):
        Settings(Settings.Y_RETRACTION_COORDINATE, spinner.value)

    @classmethod
    def onOperationsGroupingChanged(cls, dropdown: adsk.core.DropDownCommandInput):

        # Since we update the dropdown dynamically and there is no way 
        # to set an Id for the list items, we need to rely on the text 
        # of the selected item to know which one is selected.
        operationsGroupingsTexts = {
            Strings("Single file")                  : Settings.OperationsGroupings.SINGLE_FILE,
            Strings("Group on setup")               : Settings.OperationsGroupings.SETUP,
            Strings("Group on setup and tool")      : Settings.OperationsGroupings.SETUP_AND_TOOL,
            Strings("None, one file per operation") : Settings.OperationsGroupings.PER_OPERATION
        }

        Settings(Settings.OPERATIONS_GROUPING, operationsGroupingsTexts[dropdown.selectedItem.name])
        cls._updateFlatFileStructure(dropdown.parentCommand)

    @classmethod
    def onFlatFileStructureChanged(cls, checkbox: adsk.core.BoolValueCommandInput):
        Settings(Settings.FLAT_FILE_STRUCTURE, checkbox.value)

    @classmethod
    def onDeleteExistingFilesChanged(cls, checkbox: adsk.core.BoolValueCommandInput):
        Settings(Settings.DEL_FILES, checkbox.value)
    
    @classmethod
    def onDeleteOutputFolderChanged(cls, checkbox: adsk.core.BoolValueCommandInput):
        Settings(Settings.DEL_FOLDER, checkbox.value)

    @classmethod
    def onUseRegexChanged(cls, checkbox: adsk.core.BoolValueCommandInput):
        Settings(Settings.USE_REGEX, checkbox.value)
    
    @classmethod
    def onFindStringChanged(cls, input: adsk.core.StringValueCommandInput):
        Settings(Settings.FIND_STRING, input.value)

    @classmethod
    def onReplaceStringChanged(cls, input: adsk.core.StringValueCommandInput):
        Settings(Settings.REPLACE_STRING, input.value)

    @classmethod
    def onReplaceChanged(cls, checkbox: adsk.core.BoolValueCommandInput):
        Settings(Settings.REPLACE, checkbox.value)

    @classmethod
    def onInitialDelayChanged(cls, spinner: adsk.core.FloatSpinnerCommandInput):
        Settings(Settings.INITIAL_DELAY, spinner.value)

    @classmethod
    def onPostRetriesChanged(cls, spinner: adsk.core.IntegerSpinnerCommandInput):
        Settings(Settings.POST_RETRIES, spinner.value)

    @classmethod
    def onFileNameChanged(cls, input: adsk.core.StringValueCommandInput):
        Programs.Current.SetFileName(input.value)

    @classmethod
    def onSaveChanged(cls, checkbox: adsk.core.BoolValueCommandInput):
        pass # TODO: Implement saving default settings
    
    @classmethod
    def onSetupSelectedChanged(cls, checkbox: adsk.core.BoolValueCommandInput):
        setupIndex = int(checkbox.id.replace("setupSelected_", ""))
        setup = next((s for s in Setups if s.index == setupIndex), None)
        if setup and setup.isSelected != checkbox.value:
            Utils.log(f'Updating setup selection from dialog: {setup.name} selected={checkbox.value}')
            setup.select(checkbox.value)
            cls._updateDialog(checkbox.parentCommand)
    
    @classmethod
    def onHeaderCodesChanged(cls, textbox: adsk.core.TextBoxCommandInput):
        Settings(Settings.HEADER_END_CODES, textbox.text)

    @classmethod
    def onSelectAllSetupsChanged(cls, checkbox: adsk.core.BoolValueCommandInput):
        for setup in Setups:
            setup.select(checkbox.value)
        cls._updateDialog(checkbox.parentCommand)
    #endregion
