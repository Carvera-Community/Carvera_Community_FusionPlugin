from __future__ import annotations

import adsk
from ...setups.setups import Setups
from ...settings.settings import Settings
from ...strings import Strings
from ...programs import Programs

from ..dialog_constants import PostDialogConstants
from ..event_registry import EventRegistry

class GCodeTab(PostDialogConstants):

    @classmethod
    def create(cls, inputs):

        gCodeTab = inputs.addTabCommandInput(cls._GCODE_OPTIONS_GROUP_ID, Strings("G-code Options"))
        gCodeTab.isEnabled = False

        def setTabEnabled(input: adsk.core.CommandInput):
            input.parentCommand.commandInputs.itemById(cls._GCODE_OPTIONS_GROUP_ID).isEnabled = Programs.Current is not None

        EventRegistry.register(cls._PROGRAM_DROPDOWN_ID, setTabEnabled)

        setTabEnabled(gCodeTab) # initialize state based on current program selection

        #region Rotate A-Axis between setups checkbox
        rotateAAxis = gCodeTab.children.addBoolValueInput(cls._ROTATE_A_AXIS_ID, Strings('Rotate A-Axis between setups'), True, "", Settings(Settings.ROTATE_A_AXIS))
        rotateAAxis.tooltip = Strings("TOOL TIP: Rotate A-Axis between setups")
        rotateAAxis.tooltipDescription = Strings("TOOLTIP TEXT: Rotate A-Axis between setups")

        EventRegistry.register(rotateAAxis, cls._onRotateAAxisChanged) # Call custom handler below

        #endregion

        #region Retract to safe Y on A-axis rotation checkbox
        safeYRetraction = gCodeTab.children.addBoolValueInput(cls._SAFE_Y_RETRACTION_ID, Strings("Retract Y on A-axis rotation"), True, "", Settings(Settings.SAFE_Y_RETRACTION))
        safeYRetraction.tooltip = Strings("TOOL TIP: Retract Y on A-axis rotation")
        safeYRetraction.tooltipDescription = Strings("TOOLTIP TEXT: Retract Y on A-axis rotation")

        EventRegistry.register(safeYRetraction, lambda checkbox: Settings(Settings.SAFE_Y_RETRACTION, checkbox.value)) # Save settings

        def setSafeYRetractionEnabled(checkbox: adsk.core.BoolValueCommandInput):
            checkbox.parentCommand.commandInputs.itemById(cls._SAFE_Y_RETRACTION_ID).isEnabled = checkbox.value

        EventRegistry.register(safeYRetraction, lambda checkbox: Settings(Settings.SAFE_Y_RETRACTION, checkbox.value)) # Save settings
        EventRegistry.register(rotateAAxis, setSafeYRetractionEnabled) # Register handler to enable/disable based on Rotate A-Axis value
        setSafeYRetractionEnabled(rotateAAxis) # initialize state based on current value after safeYRetraction checkbox is created
        #endregion

        #region Safe Y-retraction coordinate number
        input = gCodeTab.children.addIntegerSpinnerCommandInput(cls._Y_RETRACTION_COORDINATE_ID, Strings("Safe Y-retraction coordinate (mm)"), -150, 0, 10, Settings(Settings.Y_RETRACTION_COORDINATE))
        input.tooltip = Strings("TOOL TIP: Safe Y-retraction coordinate (mm)")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Safe Y-retraction coordinate (mm)")

        EventRegistry.register(input, lambda input: Settings(Settings.Y_RETRACTION_COORDINATE, input.value))

        def setYRetractionCoordinateEnabled(checkbox: adsk.core.BoolValueCommandInput):
            inputs: adsk.core.CommandInputs = checkbox.parentCommand.commandInputs
            safeYRetractionCheckbox: adsk.core.BoolValueCommandInput = inputs.itemById(cls._SAFE_Y_RETRACTION_ID)
            yRetractionCoordinateInput: adsk.core.IntegerSpinnerCommandInput = inputs.itemById(cls._Y_RETRACTION_COORDINATE_ID)
            if yRetractionCoordinateInput is not None and safeYRetractionCheckbox is not None:
                yRetractionCoordinateInput.isEnabled = checkbox.value and safeYRetractionCheckbox.value

        EventRegistry.register(rotateAAxis, setYRetractionCoordinateEnabled) # Register handler to enable/disable based on Rotate A-Axis value
        EventRegistry.register(safeYRetraction, setYRetractionCoordinateEnabled) # Register handler to enable/disable based on Safe Y-Retraction value
        setYRetractionCoordinateEnabled(rotateAAxis) # Initialize state based on current value after Y-retraction coordinate input is created
        #endregion

        #region Restore rapid moves checkbox
        rapidMoves = gCodeTab.children.addBoolValueInput(cls._RESTORE_RAPID_MOVES_ID,Strings('Restore rapid moves'), True, "", Settings(Settings.RESTORE_RAPID_MOVES))
        rapidMoves.tooltip = Strings("TOOL TIP: Restore rapid moves")
        rapidMoves.tooltipDescription = Strings("TOOLTIP TEXT: Restore rapid moves")

        EventRegistry.register(rapidMoves, lambda checkbox: Settings(Settings.RESTORE_RAPID_MOVES, checkbox.value))
        #endregion

        #region Minimum rapid restore distance
        rapidMovesMinimumDistance = gCodeTab.children.addIntegerSpinnerCommandInput(cls._RAPID_MOVES_MINIMUM_DISTANCE_ID, Strings("Minimum rapid move distance (mm)"), 0, 50, 5, Settings(Settings.RAPID_MOVES_MINIMUM_DISTANCE))
        rapidMovesMinimumDistance.tooltip = Strings("TOOL TIP: Minimum rapid move distance (mm)")
        rapidMovesMinimumDistance.tooltipDescription = Strings("TOOLTIP TEXT: Minimum rapid move distance (mm)")

        EventRegistry.register(rapidMovesMinimumDistance, lambda input: Settings(Settings.RAPID_MOVES_MINIMUM_DISTANCE, input.value))

        def setRapidMovesMinimumDistanceEnabled(checkbox: adsk.core.BoolValueCommandInput):
            checkbox.parentCommand.commandInputs.itemById(cls._RAPID_MOVES_MINIMUM_DISTANCE_ID).isEnabled = checkbox.value

        EventRegistry.register(rapidMoves, setRapidMovesMinimumDistanceEnabled) # Register handler to enable/disable based on Restore Rapid Moves value
        setRapidMovesMinimumDistanceEnabled(rapidMoves) # Initialize state based on current value after Minimum Rapid Restore Distance input is created
        #endregion

        #region Add line numbers checkbox
        lineNumbers = gCodeTab.children.addBoolValueInput(cls._LINE_SEQUENCE_ID,Strings('Add line numbers'), True, "", Settings(Settings.LINE_SEQUENCE))
        lineNumbers.tooltip = Strings("TOOL TIP: Add line numbers")
        lineNumbers.tooltipDescription = Strings("TOOLTIP TEXT: Add line numbers")

        EventRegistry.register(lineNumbers, lambda checkbox: Settings(Settings.LINE_SEQUENCE, checkbox.value))
        #endregion

        #region Numbering digits spinner input
        lineSequenceDigits = gCodeTab.children.addIntegerSliderListCommandInput(cls._LINE_SEQUENCE_DIGITS_ID, Strings("Number of digits"), range(1, 7))
        lineSequenceDigits.valueOne = Settings(Settings.LINE_SEQUENCE_DIGITS)
        lineSequenceDigits.tooltip = Strings("TOOL TIP: Number of line digits")
        lineSequenceDigits.tooltipDescription = Strings("TOOLTIP TEXT: Number of line digits")

        EventRegistry.register(lineSequenceDigits, lambda input: Settings(Settings.LINE_SEQUENCE_DIGITS, input.valueOne))

        def setLineSequenceDigitsEnabled(checkbox: adsk.core.BoolValueCommandInput):
            checkbox.parentCommand.commandInputs.itemById(cls._LINE_SEQUENCE_DIGITS_ID).isEnabled = checkbox.value

        EventRegistry.register(lineNumbers, setLineSequenceDigitsEnabled) # Register handler to enable/disable based on Add Line Numbers value
        setLineSequenceDigitsEnabled(lineNumbers) # Initialize state based on current value after Numbering Digits input is created
        #endregion

        #region Numbering interval spinner input
        lineSequenceInterval = gCodeTab.children.addIntegerSliderListCommandInput(cls._LINE_SEQUENCE_INTERVAL_ID, Strings("Numbering interval"), [1, 2, 5, 10, 20, 50, 100])
        lineSequenceInterval.valueOne = Settings(Settings.LINE_SEQUENCE_INTERVAL)
        lineSequenceInterval.tooltip = Strings("TOOL TIP: Line numbering interval")
        lineSequenceInterval.tooltipDescription = Strings("TOOLTIP TEXT: Line numbering interval")

        EventRegistry.register(lineSequenceInterval, lambda input: Settings(Settings.LINE_SEQUENCE_INTERVAL, input.valueOne))

        def setLineSequenceIntervalEnabled(checkbox: adsk.core.BoolValueCommandInput):
            checkbox.parentCommand.commandInputs.itemById(cls._LINE_SEQUENCE_INTERVAL_ID).isEnabled = checkbox.value

        EventRegistry.register(lineNumbers, setLineSequenceIntervalEnabled) # Register handler to enable/disable based on Add Line Numbers value
        setLineSequenceIntervalEnabled(lineNumbers) # Initialize state based on current value after Numbering Interval input is created
        #endregion

        blocksGroup = gCodeTab.children.addGroupCommandInput("_GCODE_ANCHORS_GROUP_ID", Strings("G-code Blocks"))
        blocksGroup.isExpanded = False

        #region Tool change string input
        toolChangeCodes = blocksGroup.children.addTextBoxCommandInput(cls._TOOL_CHANGE_ID, Strings('Tool change code'), Settings(Settings.TOOL_CHANGE), 3, False)
        toolChangeCodes.tooltip = Strings("TOOL TIP: Tool change code")
        toolChangeCodes.tooltipDescription = Strings("TOOLTIP TEXT: Tool change code")

        EventRegistry.register(toolChangeCodes, lambda input: Settings.Set(Settings.TOOL_CHANGE, input.value))

        dummy = blocksGroup.children.addStringValueInput('', '') # As the TextBoxCommandInput above seems to be buggy we add a dummy input to create some space
        dummy.isEnabled = False
        dummy.isReadOnly = True
        #endregion

        #region Body end codes textbox input
        endCodes = blocksGroup.children.addTextBoxCommandInput(cls._END_CODES_ID, Strings('G-codes that mark ending sequence'), Settings(Settings.END_CODES), 3, False)
        endCodes.tooltip = Strings("TOOL TIP: G-codes that mark ending sequence")
        endCodes.tooltipDescription = Strings("TOOLTIP TEXT: G-codes that mark ending sequence")

        EventRegistry.register(endCodes, lambda input: Settings.Set(Settings.END_CODES, input.value))

        dummy = blocksGroup.children.addStringValueInput('', '') # As the TextBoxCommandInput above seems to be buggy we add a dummy input to create some space
        dummy.isEnabled = False
        dummy.isReadOnly = True
        #endregion

        #region Header end codes textbox input
        headerEndCodes = blocksGroup.children.addTextBoxCommandInput(cls._HEADER_CODES_ID, Strings('G-codes that mark header end'), Settings(Settings.HEADER_END_CODES), 3, False)
        headerEndCodes.tooltip = Strings("TOOL TIP: G-codes that mark header end")
        headerEndCodes.tooltipDescription = Strings("TOOLTIP TEXT: G-codes that mark header end")

        EventRegistry.register(headerEndCodes, lambda input: Settings.Set(Settings.HEADER_END_CODES, input.value))

        dummy = blocksGroup.children.addStringValueInput('', '') # As the TextBoxCommandInput above seems to be buggy we add a dummy input to create some space
        dummy.isEnabled = False
        dummy.isReadOnly = True
        #endregion


    @classmethod
    def _onRotateAAxisChanged(cls, checkbox: adsk.core.BoolValueCommandInput):
        # Always settings -> UI -> actions order to ensure that the UI state is consistent with the settings even if there are errors in the actions
        Settings(Settings.ROTATE_A_AXIS, checkbox.value)

        app = adsk.core.Application.get()
        ui = app.userInterface
        inputs = checkbox.parentCommand.commandInputs

        safeYRetractionCheckbox: adsk.core.BoolValueCommandInput = inputs.itemById(cls._SAFE_Y_RETRACTION_ID)
        if safeYRetractionCheckbox:
            safeYRetractionCheckbox.isEnabled = checkbox.value
        yRetractionCoordinateInput: adsk.core.IntegerSpinnerCommandInput = inputs.itemById(cls._Y_RETRACTION_COORDINATE_ID)
        if yRetractionCoordinateInput:
            yRetractionCoordinateInput.isEnabled = checkbox.value and safeYRetractionCheckbox.value