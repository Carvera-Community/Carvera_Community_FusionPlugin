from enum import IntEnum
from typing import Final

class Constants:
    """Contains constant values for settings keys and options."""

    # G-codes that mark the ending sequence
    END_CODES:                          Final[str] = 'endCodes'
    # If the files should be overwritten before post processing
    OVERWRITE_FILES:                    Final[str] = 'overwriteFiles'
    # If the folder should be cleared before post processing
    CLEAR_FOLDER:                       Final[str] = 'clearFolder'
    # The name of the output folder
    OUTPUT_FOLDER:                      Final[str] = 'outputFolder'
    
    # If sequence numbers should be used in file names/folders
    FILE_SEQUENCE:                      Final[str] = 'fileSequence'
    # Number of digits to use in sequence names
    FILE_SEQUENCE_DIGITS:               Final[str] = 'fileSequenceDigits'

    # If the name should be numeric
    NUMERIC_NAME:                       Final[str] = 'numericName'

    # If setups should be split into separate files
    OPERATIONS_GROUPING:                Final[str] = 'operationsGrouping'
    # If operations with the same tool should be combined
    COMBINE_TOOL:                       Final[str] = 'combineTool'

    # Settings file version
    VERSION:                            Final[str] = 'version'
    # Plugin version
    PLUGIN_VERSION:                     Final[str] = 'pluginVersion'

    # Currently selected NC Program
    NC_PROGRAM:                         Final[str] = 'ncProgram'
    # Currently selected language
    LANGUAGE:                           Final[str] = 'language'
    # If fast Z moves should be used
    RESTORE_RAPID_MOVES:                Final[str] = 'restoreRapidMoves'
    # The minimum distance to move in a rapid move to acknowledge it
    RAPID_MOVES_MINIMUM_DISTANCE:       Final[str] = 'rapidMovesMinimumDistance'
    # The maximum program steps between a start trigger if a rapid move and its end trigger
    RAPID_MOVES_MAX_STEPS:              Final[str] = 'rapidMovesMaxSteps'
    # Initial delay for retrying post processing
    INITIAL_DELAY:                      Final[str] = 'initialDelay'
    # Number of retries for post processing
    POST_RETRIES:                       Final[str] = 'postRetries'
    # If A-axis should be rotated between setups

    ROTATE_A_AXIS:                      Final[str] = 'rotateAAxis'
    # If Y-axis should be retracted while A-axis rotates
    SAFE_Y_RETRACTION:                  Final[str] = 'safeYRetraction'
    # The Y-axis coordinate to retract to when A-axis rotates
    # Note that it is a negative value as 0 is at the top of the bed
    Y_RETRACTION_COORDINATE:            Final[str] = 'yRetractionCoordinate'
    # If the folder structure should be flattened into the filenames

    FLAT_FILE_STRUCTURE:                Final[str] = 'flatFileStructure'
    # Use regular expressions for renaming setups

    USE_REGEX:                          Final[str] = 'useRegex'
    # The string to be found when renaming setups
    FIND_STRING:                        Final[str] = 'findString'
    # The string to replace the found string when renaming setups
    REPLACE_STRING:                     Final[str] = 'replaceString'
    # Replace only the Setups that is currently selected in the dialog
    REPLACE_ONLY_SELECTED:              Final[str] = 'replaceOnlySelected'
    # G-code to Precede Tool Change
    TOOL_CHANGE:                        Final[str] = 'toolChange'
    # G-codes that ends the header section
    HEADER_END_CODES:                   Final[str] = 'headerEndCodes'
    #endregion

    class OperationsGroupings(IntEnum):
        __doc__ = "Contains constant values for operation grouping options."
        SINGLE_FILE    = 0
        SETUP          = 1
        SETUP_AND_TOOL = 2
        PER_OPERATION  = 3
