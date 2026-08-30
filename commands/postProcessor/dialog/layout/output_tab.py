from pathlib import Path
from adsk.core import Application
from adsk.core import BoolValueCommandInput
from adsk.core import CommandInput
from adsk.core import DialogResults
from adsk.core import DropDownCommandInput
from adsk.core import DropDownStyles
from adsk.core import StringValueCommandInput
from adsk.core import TablePresentationStyles
from adsk.core import IntegerSliderCommandInput

from ...settings.settings import Settings
from ...strings import Strings

from ..event_registry import EventRegistry
from ..state import is_output_name_valid, numeric_name_digits
from ...programs import Programs

from ..constants import Constants

class OutputTab(Constants):
    @classmethod
    def create(cls, inputs):

        outputTab = inputs.addTabCommandInput(cls.OUTPUT_GROUP_ID, Strings("Output Options"))
        outputTab.isEnabled = False

        def setTabEnabled(dropdown: DropDownCommandInput):
            dropdown.parentCommand.commandInputs.itemById(cls.OUTPUT_GROUP_ID).isEnabled = Programs.Current is not None

        programDropdown = inputs.itemById(cls.PROGRAM_DROPDOWN_ID)
        EventRegistry.register(cls.PROGRAM_DROPDOWN_ID, setTabEnabled)
        setTabEnabled(programDropdown) # initialize state based on current program selection

        #region -- Output folder table --
        outputFolderTable = outputTab.children.addTableCommandInput(cls.OUTPUT_FOLDER_TABLE_ID, Strings('Output folder'), 2, '90:10')
        outputFolderTable.minimumVisibleRows = 2
        outputFolderTable.maximumVisibleRows = 2
        outputFolderTable.tablePresentationStyle = TablePresentationStyles.transparentBackgroundTablePresentationStyle

        #region Output folder label, spans 2 columns
        outputFolderLabel = inputs.addStringValueInput(cls.OUTPUT_FOLDER_LABEL_ID, '', Strings("Output folder"))
        outputFolderLabel.tooltip = Strings("TOOLTIP: Output folder")
        outputFolderLabel.tooltipDescription = Strings("TOOLTIP TEXT: Output folder")
        outputFolderLabel.isReadOnly = True
        outputFolderTable.addCommandInput(outputFolderLabel, 0, 0, 0, 2)

        #endregion

        #region Output folder string input

        outputFolder = inputs.addStringValueInput(cls.OUTPUT_FOLDER_ID, Strings("Output folder"), Strings("<Select program>"))
        outputFolder.tooltip = Strings("TOOLTIP: Output folder")
        outputFolder.tooltipDescription = Strings("TOOLTIP TEXT: Output folder")
        outputFolder.isReadOnly = False

        def setoutputFolder(dropdown: DropDownCommandInput):
            input = StringValueCommandInput.cast(dropdown.parentCommand.commandInputs.itemById(cls.OUTPUT_FOLDER_ID))
            try:
                if input.isValid: # Apparently the input can become invalid when the program is changed, so we check if it's valid before trying to set the value
                    newValue =  str(Programs.Current.get_output_folder().resolve()) if Programs.Current else Strings("<Select program>")
                    if input.value != newValue:
                        input.value = newValue
            except:
                pass # Every now and then the setting of the value gets an error that the object is no longer valid. Ignore and move on for now.           

        EventRegistry.register(cls.PROGRAM_DROPDOWN_ID, setoutputFolder)
        setoutputFolder(programDropdown) # initialize state based on current program selection

        outputFolderTable.addCommandInput(outputFolder, 1, 0)
        #endregion

        #region Output folder browse button

        openFolderDialogButton = inputs.addBoolValueInput(cls.OUTPUT_FOLDER_BUTTON_ID, '  …  ', False, '', False)

        outputFolderTable.addCommandInput(openFolderDialogButton, 1, 1)

        def openFolderDialog(button: BoolValueCommandInput):
            inputs = button.parentCommand.commandInputs
            app: Application = Application.get()
            ui = app.userInterface
            dialog = ui.createFolderDialog()

            dialog.initialDirectory = StringValueCommandInput.cast(inputs.itemById(cls.OUTPUT_FOLDER_ID)).value
            dialog.title = Strings("Select Output Folder")
            if dialog.showDialog() != DialogResults.DialogOK:
                return
            folder = dialog.folder
            if folder and Programs.Current is not None:
                Programs.Current.set_output_folder(Path(folder))
                StringValueCommandInput.cast(inputs.itemById(cls.OUTPUT_FOLDER_ID)).value = folder

        EventRegistry.register(cls.OUTPUT_FOLDER_BUTTON_ID, openFolderDialog)

        #endregion
        #endregion

        #region File name string input
        fileName = outputTab.children.addStringValueInput(cls.FILE_NAME_ID, Strings("File name"), Strings("<Select program>"))
        fileName.tooltip = Strings("TOOLTIP: File name")
        fileName.tooltipDescription = Strings("TOOLTIP TEXT: File name")

        def setFilename(stringInput: StringValueCommandInput):
            if Programs.Current is not None:
                Programs.Current.set_file_name(stringInput.value)

        EventRegistry.register(cls.FILE_NAME_ID, setFilename)

        def getFileNameFromProgram(dropdown: DropDownCommandInput):
            fileName = Programs.Current.fileName if Programs.Current is not None and Programs.Current.fileName is not None else Strings("<Select program>")
            StringValueCommandInput.cast(dropdown.parentCommand.commandInputs.itemById(cls.FILE_NAME_ID)).value = fileName

        EventRegistry.register(cls.PROGRAM_DROPDOWN_ID, getFileNameFromProgram)
        getFileNameFromProgram(programDropdown) # initialize state based on current program selection

        #endregion

        #region Numeric name checkbox
        numericName = outputTab.children.addBoolValueInput(cls.NUMERIC_NAME_ID, Strings("Name must be numeric"), True, "", Settings(Settings.NUMERIC_NAME))
        numericName.tooltip = Strings("TOOLTIP: Name must be numeric")
        numericName.tooltipDescription = Strings("TOOLTIP TEXT: Name must be numeric")

        EventRegistry.register(cls.NUMERIC_NAME_ID, lambda checkbox: Settings.set(Settings.NUMERIC_NAME, checkbox.value))

        def ensureNumericFileName(input: CommandInput):
            textbox = StringValueCommandInput.cast(input.parentCommand.commandInputs.itemById(cls.FILE_NAME_ID))
            numeric = BoolValueCommandInput.cast(
                textbox.parentCommand.commandInputs.itemById(cls.NUMERIC_NAME_ID)
            ).value
            textbox.isValueError = not is_output_name_valid(textbox.value, numeric)

        EventRegistry.register(cls.FILE_NAME_ID, ensureNumericFileName)
        EventRegistry.register(cls.NUMERIC_NAME_ID, ensureNumericFileName)
        ensureNumericFileName(fileName) # initialize state based on current value after file name input is created to ensure that the file name is valid if "Name must be numeric" is selected

        #endregion

        #region Prepend sequence number checkbox
        prependFileNumber = outputTab.children.addBoolValueInput(cls.FILE_SEQUENCE_ID, Strings("Prepend sequence number"), True, "", Settings(Settings.FILE_SEQUENCE))
        prependFileNumber.tooltip = Strings("TOOLTIP: Prepend file sequence number")
        prependFileNumber.tooltipDescription = Strings("TOOLTIP TEXT: Prepend file sequence number")

        EventRegistry.register(cls.FILE_SEQUENCE_ID, lambda checkbox: Settings.set(Settings.FILE_SEQUENCE, checkbox.value))
        #endregion

        #region Numbering digits spinner input
        numberingDigits = outputTab.children.addIntegerSliderListCommandInput(cls.FILE_SEQUENCE_DIGITS_ID, Strings("Number of digits"), [1, 2, 3, 4, 5, 6])
        numberingDigits.valueOne = Settings(Settings.FILE_SEQUENCE_DIGITS)
        numberingDigits.tooltip = Strings("TOOLTIP: Number of file digits")
        numberingDigits.tooltipDescription = Strings("TOOLTIP TEXT: Number of file digits")

        def setNumberingDigitsEnabled(checkbox: BoolValueCommandInput):
            checkbox.parentCommand.commandInputs.itemById(cls.FILE_SEQUENCE_DIGITS_ID).isEnabled = checkbox.value

        def setNumberingDigitsOnNumericFileName(checkbox: BoolValueCommandInput):
            input = IntegerSliderCommandInput.cast(checkbox.parentCommand.commandInputs.itemById(cls.FILE_SEQUENCE_DIGITS_ID))
            prependFileNumbers = BoolValueCommandInput.cast(checkbox.parentCommand.commandInputs.itemById(cls.FILE_SEQUENCE_ID))
            digits = numeric_name_digits(
                Programs.Current.fileName if Programs.Current else None
            )
            if checkbox.value and digits is not None:
                Settings.set(Settings.FILE_SEQUENCE_DIGITS, digits)
                input.valueOne = Settings(Settings.FILE_SEQUENCE_DIGITS)
                input.isEnabled = False
                prependFileNumbers.isEnabled = False
            else:
                prependFileNumbers.isEnabled = True
                input.isEnabled = prependFileNumbers.value

        def setNumberingDigitsOnFileName(textbox: StringValueCommandInput):
            digits = numeric_name_digits(
                Programs.Current.fileName if Programs.Current else None
            )
            if (digits is not None
                    and BoolValueCommandInput.cast(textbox.parentCommand.commandInputs.itemById(cls.NUMERIC_NAME_ID)).value):
                Settings.set(Settings.FILE_SEQUENCE_DIGITS, digits)
                IntegerSliderCommandInput.cast(textbox.commandInputs.itemById(cls.FILE_SEQUENCE_DIGITS_ID)).valueOne = Settings(Settings.FILE_SEQUENCE_DIGITS)

        EventRegistry.register(cls.FILE_SEQUENCE_DIGITS_ID, lambda spinner: Settings.set(Settings.FILE_SEQUENCE_DIGITS, spinner.valueOne))
        EventRegistry.register(cls.NUMERIC_NAME_ID, setNumberingDigitsOnNumericFileName) # Disable numbering digits when "Name must be numeric" is enabled, as it doesn't make sense in that context
        EventRegistry.register(cls.FILE_SEQUENCE_ID, setNumberingDigitsEnabled)
        EventRegistry.register(cls.FILE_NAME_ID, setNumberingDigitsOnFileName) # Disable numbering digits when "Prepend sequence number" is disabled, as it doesn't make sense in that context
        setNumberingDigitsEnabled(prependFileNumber) # initialize state based on current checkbox value
        setNumberingDigitsOnNumericFileName(numericName)
        #endregion

        #region Operations grouping dropdown
        operationsGrouping = outputTab.children.addDropDownCommandInput(cls.OPERATIONS_GROUPING_ID, Strings("Operations grouping"), DropDownStyles.TextListDropDownStyle)
        operationsGrouping.tooltip = Strings("TOOLTIP: Operations grouping")
        operationsGrouping.tooltipDescription = Strings("TOOLTIP TEXT: Operations grouping")

        operationsGroupingsTexts = {
            Strings("Single file"):                     Settings.OperationsGroupings.SINGLE_FILE,
            Strings("Group on setup"):                  Settings.OperationsGroupings.SETUP,
            Strings("Group on setup and tool"):         Settings.OperationsGroupings.SETUP_AND_TOOL,
            Strings("None, one file per operation"):    Settings.OperationsGroupings.PER_OPERATION
        }
        for grouping in operationsGroupingsTexts:
            operationsGrouping.listItems.add(grouping, operationsGroupingsTexts[grouping] == Settings(Settings.OPERATIONS_GROUPING))

        EventRegistry.register(cls.OPERATIONS_GROUPING_ID, lambda dropdown: Settings.set(Settings.OPERATIONS_GROUPING, operationsGroupingsTexts[dropdown.selectedItem.name]))
        #endregion

        #region Combine tool checkbox
        combineTools = outputTab.children.addBoolValueInput(cls.COMBINE_TOOLS_ID, Strings('Combine operations using same tool'), True, "", Settings(Settings.COMBINE_TOOL))
        combineTools.tooltip = Strings("TOOLTIP: Combine operations using same tool")
        combineTools.tooltipDescription = Strings("TOOLTIP TEXT: Combine operations using same tool")

        EventRegistry.register(cls.COMBINE_TOOLS_ID, lambda checkbox: Settings(Settings.COMBINE_TOOL, checkbox.value)) # Save settings

        #endregion


        #region Flat file structure checkbox
        flatFileStructure = outputTab.children.addBoolValueInput(cls.FLAT_FILE_STRUCTURE_ID, Strings("Flat file structure"), True, "", Settings(Settings.FLAT_FILE_STRUCTURE))
        flatFileStructure.tooltip = Strings("TOOLTIP: Flatten the file structure")
        flatFileStructure.tooltipDescription = Strings("TOOLTIP TEXT: Flatten the file structure")

        EventRegistry.register(cls.FLAT_FILE_STRUCTURE_ID, lambda checkbox: Settings.set(Settings.FLAT_FILE_STRUCTURE, checkbox.value))
        #endregion

        #region Overwrite existing files checkbox
        overwriteExistingFiles = outputTab.children.addBoolValueInput(cls.OVERWRITE_EXISTING_FILES_ID, Strings("Overwrite existing files"),  True, "", Settings(Settings.OVERWRITE_FILES))
        overwriteExistingFiles.tooltip = Strings("TOOLTIP: Overwrite existing files")
        overwriteExistingFiles.tooltipDescription = Strings("TOOLTIP TEXT: Overwrite existing files")
        overwriteExistingFiles.isEnabled = True

        EventRegistry.register(cls.OVERWRITE_EXISTING_FILES_ID, lambda checkbox: Settings(Settings.OVERWRITE_FILES, checkbox.value))
        #endregion

        #region Clear output folder checkbox
        clearOutputFolder = outputTab.children.addBoolValueInput(cls.CLEAR_OUTPUT_FOLDER_ID, Strings("Clear output folder"),  True, "", Settings(Settings.CLEAR_FOLDER))
        clearOutputFolder.tooltip = Strings("TOOLTIP: Clear output folder")
        clearOutputFolder.tooltipDescription = Strings("TOOLTIP TEXT: Clear output folder")

        def setClearOutputFolderEnabled(checkbox: BoolValueCommandInput):
            clearFolderCheckbox = BoolValueCommandInput.cast(checkbox.parentCommand.commandInputs.itemById(cls.CLEAR_OUTPUT_FOLDER_ID))
            clearFolderCheckbox.isEnabled = checkbox.value

            if not checkbox.value:
                Settings(Settings.CLEAR_FOLDER, False) # Uncheck "Clear output folder" when "Overwrite existing files" is disabled, as it doesn't make sense to clear the output folder if we're not overwriting existing files
                clearFolderCheckbox.value = False

        EventRegistry.register(cls.CLEAR_OUTPUT_FOLDER_ID, lambda checkbox: Settings.set(Settings.CLEAR_FOLDER, checkbox.value))
        EventRegistry.register(cls.OVERWRITE_EXISTING_FILES_ID, setClearOutputFolderEnabled) # Enable "Clear output folder" when "Overwrite existing files" is enabled
        setClearOutputFolderEnabled(overwriteExistingFiles) # initialize state based on current value
        #endregion -----
