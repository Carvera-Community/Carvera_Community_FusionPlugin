from __future__ import annotations

from adsk.core import TabCommandInput
from adsk.core import CommandInput
from adsk.core import BoolValueCommandInput
from adsk.core import IntegerSpinnerCommandInput

from ...settings.settings import Settings
from ...strings import Strings
from ...programs import Programs

from ..constants import Constants
from ..event_registry import EventRegistry

class GCodeTab(Constants):

    @classmethod
    def create(cls, inputs):

        gCodeTab = TabCommandInput.cast(inputs.addTabCommandInput(cls.GCODE_OPTIONS_GROUP_ID, Strings("G-code Options")))
        gCodeTab.isEnabled = False

        def setTabEnabled(input: CommandInput):
            input.parentCommand.commandInputs.itemById(cls.GCODE_OPTIONS_GROUP_ID).isEnabled = Programs.Current is not None

        EventRegistry.register(cls.PROGRAM_DROPDOWN_ID, setTabEnabled)

        setTabEnabled(gCodeTab) # initialize state based on current program selection

        #region Rotate A-Axis between setups checkbox
        rotateAAxis = gCodeTab.children.addBoolValueInput(cls.ROTATE_A_AXIS_ID, Strings('Rotate A-Axis between setups'), True, "", Settings(Settings.ROTATE_A_AXIS))
        rotateAAxis.tooltip = Strings("TOOLTIP: Rotate A-Axis between setups")
        rotateAAxis.tooltipDescription = Strings("TOOLTIP TEXT: Rotate A-Axis between setups")

        EventRegistry.register(cls.ROTATE_A_AXIS_ID, cls._onRotateAAxisChanged) # Call custom handler below

        #endregion

        #region Retract to safe Y on A-axis rotation checkbox
        safeYRetraction = gCodeTab.children.addBoolValueInput(cls.SAFE_Y_RETRACTION_ID, Strings("Retract Y on A-axis rotation"), True, "", Settings(Settings.SAFE_Y_RETRACTION))
        safeYRetraction.tooltip = Strings("TOOLTIP: Retract Y on A-axis rotation")
        safeYRetraction.tooltipDescription = Strings("TOOLTIP TEXT: Retract Y on A-axis rotation")

        EventRegistry.register(cls.SAFE_Y_RETRACTION_ID, lambda checkbox: Settings(Settings.SAFE_Y_RETRACTION, checkbox.value)) # Save settings

        def setSafeYRetractionEnabled(checkbox: BoolValueCommandInput):
            inputs = checkbox.parentCommand.commandInputs
            rotateAAxisCheckbox = BoolValueCommandInput.cast(inputs.itemById(cls.ROTATE_A_AXIS_ID))
            safeYRetractionCheckbox = BoolValueCommandInput.cast(inputs.itemById(cls.SAFE_Y_RETRACTION_ID))
            if safeYRetractionCheckbox is not None:
                safeYRetractionCheckbox.isEnabled = (rotateAAxisCheckbox is not None 
                    and rotateAAxisCheckbox.isEnabled 
                    and rotateAAxisCheckbox.value)

        EventRegistry.register(cls.SAFE_Y_RETRACTION_ID, lambda checkbox: Settings(Settings.SAFE_Y_RETRACTION, checkbox.value)) # Save settings
        EventRegistry.register(cls.ROTATE_A_AXIS_ID, setSafeYRetractionEnabled) # Register handler to enable/disable based on Rotate A-Axis value
        EventRegistry.register(cls.PROGRAM_DROPDOWN_ID, setSafeYRetractionEnabled) # If the program is changed, update the checkbox state

        setSafeYRetractionEnabled(rotateAAxis) # initialize state based on current value after safeYRetraction checkbox is created
        #endregion

        #region Safe Y-retraction coordinate number
        input = gCodeTab.children.addIntegerSpinnerCommandInput(cls.Y_RETRACTION_COORDINATE_ID, Strings("Safe Y-retraction coordinate (mm)"), -150, 0, 10, Settings(Settings.Y_RETRACTION_COORDINATE))
        input.tooltip = Strings("TOOLTIP: Safe Y-retraction coordinate (mm)")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Safe Y-retraction coordinate (mm)")

        EventRegistry.register(cls.Y_RETRACTION_COORDINATE_ID, lambda input: Settings(Settings.Y_RETRACTION_COORDINATE, input.value))

        def setYRetractionCoordinateEnabled(checkbox: CommandInput):
            inputs = checkbox.parentCommand.commandInputs
            rotateAAxisCheckbox = BoolValueCommandInput.cast(inputs.itemById(cls.ROTATE_A_AXIS_ID))
            safeYRetractionCheckbox = BoolValueCommandInput.cast(inputs.itemById(cls.SAFE_Y_RETRACTION_ID))
            yRetractionCoordinateInput = IntegerSpinnerCommandInput.cast(inputs.itemById(cls.Y_RETRACTION_COORDINATE_ID))
            if rotateAAxisCheckbox is not None and safeYRetractionCheckbox is not None and yRetractionCoordinateInput is not None:
                yRetractionCoordinateInput.isEnabled = (rotateAAxisCheckbox.isEnabled
                    and rotateAAxisCheckbox.value 
                    and safeYRetractionCheckbox.isEnabled
                    and safeYRetractionCheckbox.value)

        EventRegistry.register(cls.ROTATE_A_AXIS_ID, setYRetractionCoordinateEnabled) # Register handler to enable/disable based on Rotate A-Axis value
        EventRegistry.register(cls.SAFE_Y_RETRACTION_ID, setYRetractionCoordinateEnabled) # Register handler to enable/disable based on Safe Y-Retraction value
        EventRegistry.register(cls.PROGRAM_DROPDOWN_ID, setYRetractionCoordinateEnabled)
        setYRetractionCoordinateEnabled(rotateAAxis) # Initialize state based on current value after Y-retraction coordinate input is created
        #endregion

        #region Restore rapid moves checkbox
        rapidMoves = gCodeTab.children.addBoolValueInput(cls.RESTORE_RAPID_MOVES_ID, Strings('Restore rapid moves'), True, "", Settings(Settings.RESTORE_RAPID_MOVES))
        rapidMoves.tooltip = Strings("TOOLTIP: Restore rapid moves")
        rapidMoves.tooltipDescription = Strings("TOOLTIP TEXT: Restore rapid moves")

        EventRegistry.register(cls.RESTORE_RAPID_MOVES_ID, lambda checkbox: Settings(Settings.RESTORE_RAPID_MOVES, checkbox.value))
        #endregion

        #region Rapid moves max steps inbetween spinner input
        rapidMovesMaxSteps = gCodeTab.children.addIntegerSliderListCommandInput(cls.RAPID_MOVES_MAX_STEPS_ID, Strings("Max steps for rapid moves"), [3, 4, 5, 6, 7, 8, 9, 10])
        rapidMovesMaxSteps.valueOne = Settings(Settings.RAPID_MOVES_MAX_STEPS)
        rapidMovesMaxSteps.tooltip = Strings("TOOLTIP: Max steps for rapid moves")
        rapidMovesMaxSteps.tooltipDescription = Strings("TOOLTIP TEXT: Max steps for rapid moves")

        EventRegistry.register(cls.RAPID_MOVES_MAX_STEPS_ID, lambda spinner: Settings(Settings.RAPID_MOVES_MAX_STEPS, spinner.valueOne))
        #endregion

        #region Minimum rapid restore distance
        rapidMovesMinimumDistance = gCodeTab.children.addIntegerSpinnerCommandInput(cls.RAPID_MOVES_MINIMUM_DISTANCE_ID, Strings("Minimum rapid move distance (mm)"), 0, 50, 5, Settings(Settings.RAPID_MOVES_MINIMUM_DISTANCE))
        rapidMovesMinimumDistance.tooltip = Strings("TOOLTIP: Minimum rapid move distance (mm)")
        rapidMovesMinimumDistance.tooltipDescription = Strings("TOOLTIP TEXT: Minimum rapid move distance (mm)")

        EventRegistry.register(cls.RAPID_MOVES_MINIMUM_DISTANCE_ID, lambda input: Settings(Settings.RAPID_MOVES_MINIMUM_DISTANCE, input.value))

        def setRapidMovesMinimumDistanceEnabled(checkbox: BoolValueCommandInput):
            checkbox.parentCommand.commandInputs.itemById(cls.RAPID_MOVES_MINIMUM_DISTANCE_ID).isEnabled = checkbox.value

        EventRegistry.register(cls.RESTORE_RAPID_MOVES_ID, setRapidMovesMinimumDistanceEnabled) # Register handler to enable/disable based on Restore Rapid Moves value
        setRapidMovesMinimumDistanceEnabled(rapidMoves) # Initialize state based on current value after Minimum Rapid Restore Distance input is created
        #endregion

        blocksGroup = gCodeTab.children.addGroupCommandInput("_GCODE_ANCHORS_GROUP_ID", Strings("G-code Blocks"))
        blocksGroup.isExpanded = False

        #region Tool change string input
        toolChangeCodes = blocksGroup.children.addTextBoxCommandInput(cls.TOOL_CHANGE_ID, Strings('Tool change code'), Settings(Settings.TOOL_CHANGE), 3, False)
        toolChangeCodes.tooltip = Strings("TOOLTIP: Tool change code")
        toolChangeCodes.tooltipDescription = Strings("TOOLTIP TEXT: Tool change code")

        EventRegistry.register(cls.TOOL_CHANGE_ID, lambda input: Settings.set(Settings.TOOL_CHANGE, input.text))

        dummy = blocksGroup.children.addStringValueInput('', '') # As the TextBoxCommandInput above seems to be buggy we add a dummy input to create some space
        dummy.isEnabled = False
        dummy.isReadOnly = True
        #endregion

        #region Body end codes textbox input
        endCodes = blocksGroup.children.addTextBoxCommandInput(cls.END_CODES_ID, Strings('G-codes that mark ending sequence'), Settings(Settings.END_CODES), 3, False)
        endCodes.tooltip = Strings("TOOLTIP: G-codes that mark ending sequence")
        endCodes.tooltipDescription = Strings("TOOLTIP TEXT: G-codes that mark ending sequence")

        EventRegistry.register(cls.END_CODES_ID, lambda input: Settings.set(Settings.END_CODES, input.text))

        dummy = blocksGroup.children.addStringValueInput('', '') # As the TextBoxCommandInput above seems to be buggy we add a dummy input to create some space
        dummy.isEnabled = False
        dummy.isReadOnly = True
        #endregion

        #region Header end codes textbox input
        headerEndCodes = blocksGroup.children.addTextBoxCommandInput(cls.HEADER_CODES_ID, Strings('G-codes that mark header end'), Settings(Settings.HEADER_END_CODES), 3, False)
        headerEndCodes.tooltip = Strings("TOOLTIP: G-codes that mark header end")
        headerEndCodes.tooltipDescription = Strings("TOOLTIP TEXT: G-codes that mark header end")

        EventRegistry.register(cls.HEADER_CODES_ID, lambda input: Settings.set(Settings.HEADER_END_CODES, input.text))

        dummy = blocksGroup.children.addStringValueInput('', '') # As the TextBoxCommandInput above seems to be buggy we add a dummy input to create some space
        dummy.isEnabled = False
        dummy.isReadOnly = True
        #endregion


    @classmethod
    def _onRotateAAxisChanged(cls, checkbox: BoolValueCommandInput):
        # Always settings -> UI -> actions order to ensure that the UI state is consistent with the settings even if there are errors in the actions
        Settings(Settings.ROTATE_A_AXIS, checkbox.value)

        inputs = checkbox.parentCommand.commandInputs

        safeYRetractionCheckbox = BoolValueCommandInput.cast(inputs.itemById(cls.SAFE_Y_RETRACTION_ID))
        if safeYRetractionCheckbox:
            safeYRetractionCheckbox.isEnabled = checkbox.value
        yRetractionCoordinateInput = IntegerSpinnerCommandInput.cast(inputs.itemById(cls.Y_RETRACTION_COORDINATE_ID))
        if yRetractionCoordinateInput:
            yRetractionCoordinateInput.isEnabled = checkbox.value and safeYRetractionCheckbox.value