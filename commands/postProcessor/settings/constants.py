import enum
from typing import Final

class Constants:
    """Contains constant values for settings keys and options."""

    # G-codes that mark the ending sequence
    END_CODES:                      Final[str] = 'endCodes'
    # If the files should be deleted before post processing
    DEL_FILES:                      Final[str] = 'delFiles'
    # If the folder should be deleted before post processing
    DEL_FOLDER:                     Final[str] = 'delFolder'
    # The name of the output folder
    OUTPUT_FOLDER:                  Final[str] = 'outputFolder'
    
    # If sequence numbers should be used in file names/folders
    FILE_SEQUENCE:                  Final[str] = 'fileSequence'
    # Number of digits to use in sequence names
    FILE_SEQUENCE_DIGITS:           Final[str] = 'fileSequenceDigits'
    # The interval that the numbering should increment by
    FILE_SEQUENCE_INTERVAL:         Final[str] = 'fileSequenceInterval'

    # If sequence numbers should be used in program lines
    LINE_SEQUENCE:                  Final[str] = 'lineSequence'
    # Number of digits to use in line numbers
    LINE_SEQUENCE_DIGITS:           Final[str] = 'lineSequenceDigits'
    # The interval that the line numbering should increment by
    LINE_SEQUENCE_INTERVAL:         Final[str] = 'lineSequenceInterval'


    # If the name should be numeric
    NUMERIC_NAME:                   Final[str] = 'numericName'


    # If setups should be split into separate files
    OPERATIONS_GROUPING:            Final[str] = 'operationsGrouping'
    # If operations with the same tool should be combined
    COMBINE_TOOL:                   Final[str] = 'combineTool'

    # Settings file version
    VERSION:                        Final[str] = 'version'
    # Plugin version
    PLUGIN_VERSION:                 Final[str] = 'pluginVersion'

    # Currently selected NC Program
    NC_PROGRAM:                     Final[str] = 'ncProgram'
    # Currently selected language
    LANGUAGE:                       Final[str] = 'language'
    # If fast Z moves should be used
    RESTORE_RAPID_MOVES:            Final[str] = 'restoreRapidMoves'
    RAPID_MOVES_MINIMUM_DISTANCE:   Final[str] = 'rapidMovesMinimumDistance'
    # Initial delay for retrying post processing
    INITIAL_DELAY:                  Final[str] = 'initialDelay'
    # Number of retries for post processing
    POST_RETRIES:                   Final[str] = 'postRetries'
    # If A-axis should be rotated between setups

    ROTATE_A_AXIS:                  Final[str] = 'rotateAAxis'
    # If Y-axis should be retracted while A-axis rotates
    SAFE_Y_RETRACTION:              Final[str] = 'safeYRetraction'
    # The Y-axis coordinate to retract to when A-axis rotates
    # Note that it is a negative value as 0 is at the top of the bed
    Y_RETRACTION_COORDINATE:        Final[str] = 'yRetractionCoordinate'
    # If the folder structure should be flattened into the filenames

    FLAT_FILE_STRUCTURE:            Final[str] = 'flatFileStructure'
    # Use regular expressions for renaming setups

    USE_REGEX:                      Final[str] = 'useRegex'
    # The string to be found when renaming setups
    FIND_STRING:                    Final[str] = 'findString'
    # The string to replace the found string when renaming setups
    REPLACE_STRING:                 Final[str] = 'replaceString'

    # G-code to Precede Tool Change
    TOOL_CHANGE:                    Final[str] = 'toolChange'
    # G-codes that ends the header section
    HEADER_END_CODES:               Final[str] = 'headerEndCodes'
    #endregion

    class OperationsGroupings():
        __doc__ = "Contains constant values for operation grouping options."
        SINGLE_FILE:    Final[int] = 0
        SETUP:          Final[int] = 1
        SETUP_AND_TOOL: Final[int] = 2
        PER_OPERATION:  Final[int] = 3
