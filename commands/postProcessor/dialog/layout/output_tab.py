from pathlib import Path
import adsk.core
from ...settings.settings import Settings
from ...strings import Strings

from ..event_registry import EventRegistry
from ...programs import Programs

from ..dialog_constants import PostDialogConstants

class OutputTab(PostDialogConstants):
    @classmethod
    def create(cls, inputs):

        outputTab = inputs.addTabCommandInput(cls._OUTPUT_GROUP_ID, Strings("Output Options"))
        outputTab.isEnabled = False

        def setTabEnabled(dropdown: adsk.core.DropDownCommandInput):
            dropdown.parentCommand.commandInputs.itemById(cls._OUTPUT_GROUP_ID).isEnabled = Programs.Current is not None

        programDropdown = inputs.itemById(cls._PROGRAM_DROPDOWN_ID)
        EventRegistry.register(programDropdown, setTabEnabled)
        setTabEnabled(programDropdown) # initialize state based on current program selection

        #region -- Output folder table --
        outputFolderTable = outputTab.children.addTableCommandInput(cls._OUTPUT_FOLDER_TABLE_ID, Strings('Output folder'), 2, '90:10')
        outputFolderTable.minimumVisibleRows = 2
        outputFolderTable.maximumVisibleRows = 2
        outputFolderTable.tablePresentationStyle = adsk.core.TablePresentationStyles.transparentBackgroundTablePresentationStyle

        #region Output folder label, spans 2 columns
        outputFolderLabel = inputs.addStringValueInput(cls._OUTPUT_FOLDER_LABEL_ID, '', Strings("Output folder"))
        outputFolderLabel.tooltip = Strings("TOOL TIP: Output folder")
        outputFolderLabel.tooltipDescription = Strings("TOOLTIP TEXT: Output folder")
        outputFolderLabel.isReadOnly = True
        outputFolderTable.addCommandInput(outputFolderLabel, 0, 0, 0, 2)

        #endregion

        #region Output folder string input

        outputFolder = inputs.addStringValueInput(cls._OUTPUT_FOLDER_ID, Strings("Output folder"), Strings("<Select program>"))
        outputFolder.tooltip = Strings("TOOL TIP: Output folder")
        outputFolder.tooltipDescription = Strings("TOOLTIP TEXT: Output folder")
        outputFolder.isReadOnly = False

        def setoutputFolder(dropdown: adsk.core.DropDownCommandInput):
            input: adsk.core.StringValueCommandInput = dropdown.parentCommand.commandInputs.itemById(cls._OUTPUT_FOLDER_ID)
            try:
                if input.isValid: # Apparently the input can become invalid when the program is changed, so we check if it's valid before trying to set the value
                    newValue =  str(Programs.Current.GetOutputFolder().resolve()) if Programs.Current else Strings("<Select program>")
                    if input.value != newValue:
                        input.value = newValue
            except:
                pass # Every now and then the setting of the value gets an error that the object is no longer valid. Ignore and move on for now.           

        EventRegistry.register(programDropdown, setoutputFolder)
        setoutputFolder(programDropdown) # initialize state based on current program selection

        outputFolderTable.addCommandInput(outputFolder, 1, 0)
        #endregion

        #region Output folder browse button

        openFolderDialogButton = inputs.addBoolValueInput(cls._OUTPUT_FOLDER_BUTTON_ID, '  …  ', False, '', False)

        outputFolderTable.addCommandInput(openFolderDialogButton, 1, 1)

        def openFolderDialog(button: adsk.core.BoolValueCommandInput):
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

        EventRegistry.register(openFolderDialogButton, openFolderDialog)

        #endregion
        #endregion

        #region File name string input
        fileName = outputTab.children.addStringValueInput(cls._FILE_NAME_ID, Strings("File name"), Strings("<Select program>"))
        fileName.tooltip = Strings("TOOL TIP: File name")
        fileName.tooltipDescription = Strings("TOOLTIP TEXT: File name")

        def setFilename(stringInput: adsk.core.StringValueCommandInput):
            if Programs.Current is not None:
                Programs.Current.SetFileName(stringInput.value)

        EventRegistry.register(fileName, setFilename)

        def getFileNameFromProgram(dropdown: adsk.core.DropDownCommandInput):
            dropdown.parentCommand.commandInputs.itemById(cls._FILE_NAME_ID).value = Programs.Current.fileName if Programs.Current else Strings("<Select program>")

        EventRegistry.register(programDropdown, getFileNameFromProgram)
        getFileNameFromProgram(programDropdown) # initialize state based on current program selection

        #endregion

        #region Numeric name checkbox
        numericName = outputTab.children.addBoolValueInput(cls._NUMERIC_NAME_ID, Strings("Name must be numeric"), True, "", Settings(Settings.NUMERIC_NAME))
        numericName.tooltip = Strings("TOOL TIP: Name must be numeric")
        numericName.tooltipDescription = Strings("TOOLTIP TEXT: Name must be numeric")

        EventRegistry.register(numericName, lambda checkbox: Settings.Set(Settings.NUMERIC_NAME, checkbox.value))

        def ensureNumericFileName(input: adsk.core.CommandInput):
            textbox = input.parentCommand.commandInputs.itemById(cls._FILE_NAME_ID)
            textbox.isValueError = len(textbox.value) == 0 \
                or (textbox.parentCommand.commandInputs.itemById(cls._NUMERIC_NAME_ID).value 
                    and not textbox.value.isnumeric())

        EventRegistry.register(fileName, ensureNumericFileName)
        EventRegistry.register(numericName, ensureNumericFileName)
        ensureNumericFileName(fileName) # initialize state based on current value after file name input is created to ensure that the file name is valid if "Name must be numeric" is selected

        #endregion

        #region Prepend sequence number checkbox
        prependFileNumber = outputTab.children.addBoolValueInput(cls._FILE_SEQUENCE_ID, Strings("Prepend sequence number"), True, "", Settings(Settings.FILE_SEQUENCE))
        prependFileNumber.tooltip = Strings("TOOL TIP: Prepend file sequence number")
        prependFileNumber.tooltipDescription = Strings("TOOLTIP TEXT: Prepend file sequence number")

        EventRegistry.register(prependFileNumber, lambda checkbox: Settings.Set(Settings.FILE_SEQUENCE, checkbox.value))
        #endregion

        #region Numbering digits spinner input
        numberingDigits = outputTab.children.addIntegerSliderListCommandInput(cls._FILE_SEQUENCE_DIGITS_ID, Strings("Number of digits"), [1, 2, 3, 4, 5, 6])
        numberingDigits.valueOne = Settings(Settings.FILE_SEQUENCE_DIGITS)
        numberingDigits.tooltip = Strings("TOOL TIP: Number of file digits")
        numberingDigits.tooltipDescription = Strings("TOOLTIP TEXT: Number of file digits")

        def setNumberingDigitsEnabled(checkbox: adsk.core.BoolValueCommandInput):
            checkbox.parentCommand.commandInputs.itemById(cls._FILE_SEQUENCE_DIGITS_ID).isEnabled = checkbox.value

        def setNumberingDigitsOnNumericFileName(checkbox: adsk.core.BoolValueCommandInput):
            input = checkbox.parentCommand.commandInputs.itemById(cls._FILE_SEQUENCE_DIGITS_ID)
            prependFileNumbers = checkbox.parentCommand.commandInputs.itemById(cls._FILE_SEQUENCE_ID)
            if checkbox.value and Programs.Current and Programs.Current.fileName.isnumeric():
                Settings.Set(Settings.FILE_SEQUENCE_DIGITS, min(len(Programs.Current.fileName), 6))
                input.valueOne = Settings(Settings.FILE_SEQUENCE_DIGITS)
                input.isEnabled = False
                prependFileNumbers.isEnabled = False
            else:
                prependFileNumbers.isEnabled = True
                input.isEnabled = prependFileNumbers.value

        def setNumberingDigitsOnFileName(textbox: adsk.core.StringValueCommandInput):
            if Programs.Current and Programs.Current.fileName.isnumeric() and textbox.parentCommand.commandInputs.itemById(cls._NUMERIC_NAME_ID).value:
                Settings.Set(Settings.FILE_SEQUENCE_DIGITS, min(len(Programs.Current.fileName), 6))
                textbox.commandInputs.itemById(cls._FILE_SEQUENCE_DIGITS_ID).valueOne = Settings(Settings.FILE_SEQUENCE_DIGITS)

        EventRegistry.register(numberingDigits, lambda spinner: Settings.Set(Settings.FILE_SEQUENCE_DIGITS, spinner.valueOne))
        EventRegistry.register(cls._NUMERIC_NAME_ID, setNumberingDigitsOnNumericFileName) # Disable numbering digits when "Name must be numeric" is enabled, as it doesn't make sense in that context
        EventRegistry.register(prependFileNumber, setNumberingDigitsEnabled)
        EventRegistry.register(cls._FILE_NAME_ID, setNumberingDigitsOnFileName) # Disable numbering digits when "Prepend sequence number" is disabled, as it doesn't make sense in that context
        setNumberingDigitsEnabled(prependFileNumber) # initialize state based on current checkbox value
        setNumberingDigitsOnNumericFileName(numericName)
        #endregion

        #region Numbering interval spinner input
        numberingInterval = outputTab.children.addIntegerSliderListCommandInput(cls._FILE_SEQUENCE_INTERVAL_ID, Strings("Numbering interval"), [1, 2, 5, 10, 20])
        numberingInterval.valueOne = Settings(Settings.FILE_SEQUENCE_INTERVAL)  
        numberingInterval.tooltip = Strings("TOOL TIP: File numbering interval")
        numberingInterval.tooltipDescription = Strings("TOOLTIP TEXT: File numbering interval")

        def setNumberingIntervalEnabled(checkbox: adsk.core.BoolValueCommandInput):
            checkbox.parentCommand.commandInputs.itemById(cls._FILE_SEQUENCE_INTERVAL_ID).isEnabled = checkbox.value

        EventRegistry.register(numberingInterval, lambda spinner: Settings.Set(Settings.FILE_SEQUENCE_INTERVAL, spinner.valueOne))
        EventRegistry.register(prependFileNumber, setNumberingIntervalEnabled)
        setNumberingIntervalEnabled(prependFileNumber) # initialize state based on current checkbox value
        #endregion

        #region Operations grouping dropdown
        operationsGrouping = outputTab.children.addDropDownCommandInput(cls._OPERATIONS_GROUPING_ID, Strings("Operations grouping"), adsk.core.DropDownStyles.TextListDropDownStyle)
        operationsGrouping.tooltip = Strings("TOOL TIP: Operations grouping")
        operationsGrouping.tooltipDescription = Strings("TOOLTIP TEXT: Operations grouping")

        operationsGroupingsTexts = {
            Strings("Single file"):                     Settings.OperationsGroupings.SINGLE_FILE,
            Strings("Group on setup"):                  Settings.OperationsGroupings.SETUP,
            Strings("Group on setup and tool"):         Settings.OperationsGroupings.SETUP_AND_TOOL,
            Strings("None, one file per operation"):    Settings.OperationsGroupings.PER_OPERATION
        }
        for grouping in operationsGroupingsTexts:
            operationsGrouping.listItems.add(grouping, operationsGroupingsTexts[grouping] == Settings(Settings.OPERATIONS_GROUPING))

        EventRegistry.register(operationsGrouping, lambda dropdown: Settings.Set(Settings.OPERATIONS_GROUPING, operationsGroupingsTexts[dropdown.selectedItem.name]))
        #endregion

        #region Combine tool checkbox
        combineTools = outputTab.children.addBoolValueInput(cls._COMBINE_TOOLS_ID, Strings('Combine operations using same tool'), True, "", Settings(Settings.COMBINE_TOOL))
        combineTools.tooltip = Strings("TOOL TIP: Combine operations using same tool")
        combineTools.tooltipDescription = Strings("TOOLTIP TEXT: Combine operations using same tool")

        EventRegistry.register(cls._COMBINE_TOOLS_ID, lambda checkbox: Settings(Settings.COMBINE_TOOL, checkbox.value)) # Save settings

        #endregion


        #region Flat file structure checkbox
        flatFileStructure = outputTab.children.addBoolValueInput(cls._FLAT_FILE_STRUCTURE_ID, Strings("Flat file structure"), True, "", Settings(Settings.FLAT_FILE_STRUCTURE))
        flatFileStructure.tooltip = Strings("TOOL TIP: Flatten the file structure")
        flatFileStructure.tooltipDescription = Strings("TOOLTIP TEXT: Flatten the file structure")

        EventRegistry.register(flatFileStructure, lambda checkbox: Settings.Set(Settings.FLAT_FILE_STRUCTURE, checkbox.value))
        #endregion

        #region Delete existing files checkbox
        deleteExistingFiles = outputTab.children.addBoolValueInput(cls._DELETE_EXISTING_FILES_ID, Strings("Overwrite existing files"),  True, "", Settings(Settings.DEL_FILES))
        deleteExistingFiles.tooltip = Strings("TOOL TIP: Overwrite existing files")
        deleteExistingFiles.tooltipDescription = Strings("TOOLTIP TEXT: Overwrite existing files")
        deleteExistingFiles.isEnabled = True

        EventRegistry.register(deleteExistingFiles, lambda checkbox: Settings.Set(Settings.DEL_FILES, checkbox.value))
        #endregion

        #region Delete output folder checkbox
        deleteOutputFolder = outputTab.children.addBoolValueInput(cls._DELETE_OUTPUT_FOLDER_ID, Strings("Clear output folder"),  True, "", Settings(Settings.DEL_FOLDER))
        deleteOutputFolder.tooltip = Strings("TOOL TIP: Clear output folder")
        deleteOutputFolder.tooltipDescription = Strings("TOOLTIP TEXT: Clear output folder")

        EventRegistry.register(deleteOutputFolder, lambda checkbox: Settings.Set(Settings.DEL_FOLDER, checkbox.value))
        EventRegistry.register(deleteExistingFiles, lambda checkbox: setattr(checkbox.parentCommand.commandInputs.itemById(cls._DELETE_OUTPUT_FOLDER_ID), 'isEnabled', checkbox.value)) # Enable "Clear output folder" when "Overwrite existing files" is enabled
        #endregion -----

