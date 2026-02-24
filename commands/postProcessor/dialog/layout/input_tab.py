from ast import Tuple
import adsk.core
from adsk.core import DropDownStyles
from .....lib.fusionAddInUtils.general_utils import Utils

from ...const import Const
from ...settings.settings import Settings

from ...programs import Programs
from ...setups.setups import Setups
from ...setups.setup.setup import Setup
from ...strings import Strings

from ..dialog_constants import PostDialogConstants
from ..event_registry import EventRegistry

class InputTab(PostDialogConstants):

    previous = None

    @classmethod
    def create(cls, inputs):

        # helper method to make the syntax a little easier for adding 
        # items to a table.
        def init(obj, **attrs):
            for k, v in attrs.items():
                setattr(obj, k, v)
            return obj
        
        inputTab = inputs.addTabCommandInput(cls._INPUT_SELECTION_TAB_ID, Strings("Input Selection"))
        inputTab.activate()

        #region Program dropdown
        programDropdown = inputTab.children.addDropDownCommandInput(cls._PROGRAM_DROPDOWN_ID, Strings('NC Program'), DropDownStyles.TextListDropDownStyle)
        programDropdown.tooltip = Strings("TOOLTIP: NC Program to Use")
        programDropdown.tooltipDescription = Strings("TOOLTIP TEXT: NC Program to Use")

        EventRegistry.register(programDropdown, cls._onProgramChanged)

        # Populate the dropdown with available programs
        for program in Programs:
            if not program.hasError and not program.isEmpty and not program.isSuppressed:
                programDropdown.listItems.add(program.name, Settings(Settings.NC_PROGRAM) == program.name)
        programDropdown.isEnabled = True
        #endregion

        #region Program machine text field
        machineInput = inputTab.children.addStringValueInput(cls._MACHINE_ID, Strings('Machine'), Strings('<Select a program>'))
        machineInput.tooltip = Strings("TOOLTIP: Machine")
        machineInput.tooltipDescription = Strings("TOOLTIP TEXT: Machine")
        machineInput.isReadOnly = True
        machineInput.isEnabled = False

        def setMachineValue(programDropdown):
            machineText = programDropdown.parentCommand.commandInputs.itemById(cls._MACHINE_ID)
            machineText.isEnabled =  Programs.Current is not None and Programs.Current.hasMachine
            machineText.value = Programs.Current.machineName if machineText.isEnabled else Strings('<Select a program with a machine configuration>')

        EventRegistry.register(programDropdown, setMachineValue)  

        # Set initial state of machine input based on whether a program is already selected
        setMachineValue(programDropdown)
        #endregion

        #region Post Processor text field
        postProcessorInput = inputTab.children.addStringValueInput(cls._POST_PROCESSOR_ID, Strings('Post Processor'), Strings('<Select a program>'))
        postProcessorInput.tooltip = Strings("TOOLTIP: Post Processor")
        postProcessorInput.tooltipDescription = Strings("TOOLTIP TEXT: Post Processor")
        postProcessorInput.isReadOnly = True
        postProcessorInput.isEnabled = False

        def setPostProcessorValue(programDropdown):
            postProcessorText = programDropdown.parentCommand.commandInputs.itemById(cls._POST_PROCESSOR_ID)
            postProcessorText.isEnabled = Programs.Current is not None and Programs.Current.hasPostProcessor
            postProcessorText.value = Programs.Current.postProcessorDescription if postProcessorText.isEnabled else Strings('<Select a program with a post processor>')

        EventRegistry.register(programDropdown, setPostProcessorValue)

        setPostProcessorValue(programDropdown) # Set initial state of post processor input based on whether a program is already selected
        #endregion

        #region Setups table
        setupsTable = inputTab.children.addTableCommandInput('SetupsTable', '',5, "6:31:21:21:21") # 5 columns with relative widths of 6, 31, 21, 21, 21 (100[%] is easier)
        setupsTable.minimumVisibleRows = 3
        setupsTable.maximumVisibleRows = min(10, max(3, len([setup for setup in Setups if not (setup.hasError or setup.isSuppressed)]) + 1)) # +1 for the header row

        selectAllSetups = inputs.addBoolValueInput(cls._SELECT_ALL_SETUPS_ID, '', True, '', False)

        def setAllSetups(checkbox):
            for setup in Setups:
                if not setup.hasError and not setup.isSuppressed:
                    setup.Select(checkbox.value)
            cls._updateSetups(checkbox) # Update the table to enable/disable inputs based on the new selection
            
        EventRegistry.registerWithOnlyChange(selectAllSetups, setAllSetups) # For some reason the checkbox generates duplicate events, so we use a special registry method that ignores duplicates. See EventRegistry for details.

        row = 0
        # Add header row
        setupsTable.addCommandInput(selectAllSetups, row, 0)
        setupsTable.addCommandInput(
                init(inputs.addStringValueInput('', '', Strings('Setup Name')),
                isReadOnly = True
            ), row, 1)
        setupsTable.addCommandInput(
                init(inputs.addStringValueInput('', '', Strings('Origin')),
                isReadOnly = True
            ), row, 2)
        setupsTable.addCommandInput(
                init(inputs.addStringValueInput('', '', Strings('Parallel')),
                isReadOnly = True
            ), row, 3)
        setupsTable.addCommandInput(
                init(inputs.addStringValueInput('', '', Strings('Rotation')),
                isReadOnly = True
            ), row, 4)
        
        # Creating callback for when a setup selection has changed and the table needs update.
        def onSetupChanged(checkbox):
            setupIndex = int(checkbox.id.replace("setupSelected_", ""))
            setup = next((s for s in Setups if s.index == setupIndex), None)
            if setup and setup.isSelected != checkbox.value:
                Utils.log(f'Updating setup selection from dialog: {setup.name} selected={checkbox.value}')
                setup.Select(checkbox.value)
                cls._updateSetups(checkbox) # Update the table to enable/disable inputs based on the new selection
                EventRegistry.setValue(cls._SELECT_ALL_SETUPS_ID, areAllSetupsSelected(checkbox.parentCommand.commandInputs))

        def areAllSetupsSelected(inputs) -> bool:
            for s in Setups:
                if s.hasError or s.isSuppressed:
                    continue
                checkbox = inputs.itemById(f"setupSelected_{s.index}")
                if checkbox is None: # Should not happen...
                    return False
                if not checkbox.isEnabled:
                    continue
                if not checkbox.value:
                    return False
            return True
        
        # Wiring up event so that when the A-axis option is changed, 
        # the checkbox enabling de-/selecting all enabled setups is 
        # updated to reflect the new state.
        EventRegistry.register(cls._ROTATE_A_AXIS_ID, lambda input: EventRegistry.setValue(cls._SELECT_ALL_SETUPS_ID, areAllSetupsSelected(input.parentCommand.commandInputs)))
        
        def updateSetupsWithNotice(input: adsk.core.CommandInput):
            needsRotation, rotatedSetups = Setups.AAxisRotationRequired()
            if needsRotation and not input.value:
                input.parentCommand.commandInputs.itemById(cls._INPUT_SELECTION_TAB_ID).activate()
                app = adsk.core.Application.get()
                ui = app.userInterface
                if ui.messageBox(
                        Strings("Some setups will be deselected as they are rotated. <p>Rotated setups:<ul>{rotatedSetups}</ul><p>Do you want to continue?")
                            .format(rotatedSetups = ''.join([Strings("<li>{name}: {degrees}°</li>")
                                                            .format(name=name, degrees=degrees) for name, degrees in rotatedSetups])),
                        Const.CMD_NAME,
                        adsk.core.MessageBoxButtonTypes.OKCancelButtonType,
                        adsk.core.MessageBoxIconTypes.InformationIconType) != adsk.core.DialogResults.DialogOK:
                    input.value = not input.value # revert the change if user cancels
            cls._updateSetups(input)

        EventRegistry.register(cls._ROTATE_A_AXIS_ID, updateSetupsWithNotice) # If the Rotate A-Axis option is changed, some setups may become ineligible for selection and need to be updated in the table.

        # Add setup rows
        for setup in Setups:
            if setup.hasError or setup.isSuppressed:
                continue

            row += 1
            setupCheckbox = inputs.addBoolValueInput(f"setupSelected_{setup.index}", '', True, '', setup.isSelected)
            EventRegistry.register(setupCheckbox, onSetupChanged)
            setupsTable.addCommandInput(setupCheckbox, row, 0)
            setupsTable.addCommandInput(
                init(inputs.addStringValueInput(f"setupName_{setup.index}", '', setup.name),
                    isReadOnly = True,
                    isEnabled = setup.isSelected
                ),row,1)
            setupsTable.addCommandInput(
                init(inputs.addStringValueInput(f"setupOrigin_{setup.index}", '', ''),
                    isReadOnly = True,
                    isEnabled = setup.isSelected
                ),row,2)
            setupsTable.addCommandInput(
                init(inputs.addStringValueInput(f"setupXNormal_{setup.index}", '', ''),
                    isReadOnly = True,
                    isEnabled = setup.isSelected
                ),row,3)
            setupsTable.addCommandInput(
                init(inputs.addStringValueInput(f"setupARotation_{setup.index}", '', ''),
                    isReadOnly = True,
                    isEnabled = setup.isSelected
                ),row,4)
        
        EventRegistry.register(programDropdown, cls._updateSetups)
        #endregion

    @classmethod
    def _onProgramChanged(cls, dropdown: adsk.core.DropDownCommandInput):
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

    @classmethod
    def _updateSetups(cls, input: adsk.core.CommandInput):
        """Updates the setups table in the dialog, enabling/disabling 
        rows and setting values based on the selected program and 
        settings."""
        inputs = input.parentCommand.commandInputs
        rotateAAxisCheckbox: adsk.core.BoolValueCommandInput = inputs.itemById(cls._ROTATE_A_AXIS_ID)
        rotateAAxisCheckbox.isEnabled = False if Programs.Current is None else Programs.Current.machineHasAAxis

        validProgram = Programs.Current is not None and Programs.Current.hasMachine

        firstSetup: Setup = None
        for setup in Setups:

            if setup.hasError or setup.isSuppressed:
                continue

            rotation = 0 if firstSetup is None else round(setup.GetRotationAroundXAxisRelativeToDeg(firstSetup), 3)
            rowState = cls._getSetupRowState(
                setup,
                firstSetup is not None,
                validProgram,
                setup.origin.isEqualTo(firstSetup.origin) if firstSetup is not None else True,
                setup.xNormal.isParallelTo(firstSetup.xNormal) if firstSetup is not None else True,
                rotateAAxisCheckbox.value,
                rotation)

            cls._setTableRowValues(inputs, rowState)
            
            setup.Select(rowState[cls._SELECTED]) # Update the setup's selected state based on the value in the table, which may have been changed if the setup became ineligible for selection

            if firstSetup is None and setup.isSelected:
                firstSetup = setup


    @classmethod
    def _isSetupSelectable(cls, 
                           firstSetup: Setup, 
                           validProgram: bool, 
                           sameOrigin: bool, 
                           parallelXAxis: bool, 
                           canRotate: bool, 
                           requiredRotation: float
                        ) -> bool:
        if firstSetup is None:
            return True
        return sameOrigin \
            and parallelXAxis \
            and validProgram \
            and (requiredRotation == 0 \
                or (Programs.Current.machineHasAAxis \
                    and canRotate))

    _INDEX = "index"
    _ENABLED = "enabled"
    _SELECTED = "selected"
    _NAME = "name"
    _ORIGIN = "origin"
    _X_NORMAL = "xNormal"
    _ROTATION = "rotation"

    @classmethod
    def _getSetupRowState(cls, 
                        setup: Setup,
                        hasReference: bool,
                        validProgram: bool,
                        sameOrigin: bool,
                        parallelXAxis: bool,
                        canRotate: bool,
                        rotation: float
                    ) -> Tuple[bool, bool, str, str, str]:
        """Determines the enabled state, selected state, and displayed 
        origin, xNormal, and rotation values for a given setup row in 
        the table based on the setup's properties and the current 
        program selection."""
        
        isSelectable = cls._isSetupSelectable(
                                not hasReference,
                                validProgram,
                                sameOrigin,
                                parallelXAxis,  
                                canRotate, 
                                rotation)

        isEnabled = isSelectable
        isSelected = setup.isSelected if isSelectable else False

        if hasReference:
            originText = Strings("Same") if sameOrigin else Strings("Different")
            xNormalText = Strings("Aligned") if parallelXAxis else Strings("Misaligned") 
            rotationText = f"{rotation}°" if parallelXAxis else ''
        else:
            originText = xNormalText = rotationText = Strings("(reference)") if isSelected else '-'

        return {
            cls._INDEX: setup.index,
            cls._NAME: setup.name,
            cls._ENABLED: isEnabled, 
            cls._SELECTED: isSelected, 
            cls._ORIGIN: originText, 
            cls._X_NORMAL: xNormalText, 
            cls._ROTATION: rotationText
        }

    @classmethod
    def _setTableRowValues(cls, inputs, rowState: dict):
        """Sets the enabled state and values of the inputs in a given 
        row of the setups table based on the provided row state."""

        inputCheckbox: adsk.core.BoolValueCommandInput = inputs.itemById(f"setupSelected_{rowState[cls._INDEX]}")
        setupName: adsk.core.TextBoxCommandInput = inputs.itemById(f"setupName_{rowState[cls._INDEX]}")
        origin: adsk.core.TextBoxCommandInput = inputs.itemById(f"setupOrigin_{rowState[cls._INDEX]}")
        xNormalInput: adsk.core.TextBoxCommandInput = inputs.itemById(f"setupXNormal_{rowState[cls._INDEX]}")
        aRotation: adsk.core.TextBoxCommandInput = inputs.itemById(f"setupARotation_{rowState[cls._INDEX]}")

        inputCheckbox.isEnabled = rowState[cls._ENABLED]
        setupName.value = rowState[cls._NAME]
        setupName.isEnabled = rowState[cls._ENABLED]
        origin.isEnabled = rowState[cls._ENABLED]
        xNormalInput.isEnabled = rowState[cls._ENABLED]
        aRotation.isEnabled = rowState[cls._ENABLED]

        inputCheckbox.value = rowState[cls._SELECTED]
        origin.value = rowState[cls._ORIGIN]
        xNormalInput.value = rowState[cls._X_NORMAL]
        aRotation.value = rowState[cls._ROTATION]
