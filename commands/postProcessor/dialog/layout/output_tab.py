from pathlib import Path
from adsk.core import Application
from adsk.core import BoolValueCommandInput
from adsk.core import CommandInput
from adsk.core import DialogResults
from adsk.core import DropDownCommandInput
from adsk.core import StringValueCommandInput
from adsk.core import TablePresentationStyles
from adsk.core import IntegerSliderCommandInput

from ...settings.settings import Settings
from ...strings import Strings

from ..event_registry import EventRegistry
from ..state import is_output_folder_valid, is_output_name_valid, numeric_name_digits
from ...programs import Programs

from ..constants import Constants
from .output_grouping_section import create_grouping_and_safety_options

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
            except RuntimeError:
                pass # Every now and then the setting of the value gets an error that the object is no longer valid. Ignore and move on for now.           

        EventRegistry.register(cls.PROGRAM_DROPDOWN_ID, setoutputFolder)
        setoutputFolder(programDropdown) # initialize state based on current program selection

        def applyOutputFolder(stringInput: StringValueCommandInput):
            valid = is_output_folder_valid(stringInput.value)
            stringInput.isValueError = not valid
            if valid and Programs.Current is not None:
                Programs.Current.set_output_folder(Path(stringInput.value).expanduser())

        # Fusion delivers StringValueCommandInput changes when editing is
        # committed (normally when focus leaves the field).
        EventRegistry.register(cls.OUTPUT_FOLDER_ID, applyOutputFolder)

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
            fileName = Programs.Current.file_name if Programs.Current is not None and Programs.Current.file_name is not None else Strings("<Select program>")
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
            fileNameInput = StringValueCommandInput.cast(checkbox.parentCommand.commandInputs.itemById(cls.FILE_NAME_ID))
            digits = numeric_name_digits(fileNameInput.value)
            if checkbox.value:
                if digits is not None:
                    Settings.set(Settings.FILE_SEQUENCE_DIGITS, digits)
                    input.valueOne = Settings(Settings.FILE_SEQUENCE_DIGITS)
                input.isEnabled = False
                prependFileNumbers.isEnabled = False
            else:
                prependFileNumbers.isEnabled = True
                input.isEnabled = prependFileNumbers.value

        def setNumberingDigitsOnFileName(textbox: StringValueCommandInput):
            inputs = textbox.parentCommand.commandInputs
            digits = numeric_name_digits(textbox.value)
            if (digits is not None
                    and BoolValueCommandInput.cast(inputs.itemById(cls.NUMERIC_NAME_ID)).value):
                Settings.set(Settings.FILE_SEQUENCE_DIGITS, digits)
                IntegerSliderCommandInput.cast(inputs.itemById(cls.FILE_SEQUENCE_DIGITS_ID)).valueOne = Settings(Settings.FILE_SEQUENCE_DIGITS)
            setNumberingDigitsOnNumericFileName(BoolValueCommandInput.cast(inputs.itemById(cls.NUMERIC_NAME_ID)))

        EventRegistry.register(cls.FILE_SEQUENCE_DIGITS_ID, lambda spinner: Settings.set(Settings.FILE_SEQUENCE_DIGITS, spinner.valueOne))
        EventRegistry.register(cls.NUMERIC_NAME_ID, setNumberingDigitsOnNumericFileName) # Disable numbering digits when "Name must be numeric" is enabled, as it doesn't make sense in that context
        EventRegistry.register(cls.FILE_SEQUENCE_ID, setNumberingDigitsEnabled)
        EventRegistry.register(cls.FILE_NAME_ID, setNumberingDigitsOnFileName) # Disable numbering digits when "Prepend sequence number" is disabled, as it doesn't make sense in that context
        setNumberingDigitsEnabled(prependFileNumber) # initialize state based on current checkbox value
        setNumberingDigitsOnNumericFileName(numericName)
        #endregion

        create_grouping_and_safety_options(outputTab, cls)
