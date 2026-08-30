from dataclasses import dataclass

from .settings.constants import Constants
from .settings.settings import Settings


@dataclass(frozen=True)
class ProcessingSettings:
    operationsGrouping: Constants.OperationsGroupings
    combineTool: bool
    flatFileStructure: bool
    numericName: bool
    clearFolder: bool
    fileSequence: bool
    fileSequenceDigits: int
    overwriteFiles: bool
    rotateAAxis: bool
    safeYRetraction: bool
    yRetractionCoordinate: float
    restoreRapidMoves: bool
    rapidMovesMinimumDistance: float
    rapidMovesMaxSteps: int
    headerEndCodes: str
    endCodes: str

    @classmethod
    def capture(cls) -> "ProcessingSettings":
        minimum_distance = Settings.Get(Settings.RAPID_MOVES_MINIMUM_DISTANCE)
        maximum_steps = Settings.Get(Settings.RAPID_MOVES_MAX_STEPS)
        return cls(
            operationsGrouping=Settings.Get(Settings.OPERATIONS_GROUPING),
            combineTool=bool(Settings.Get(Settings.COMBINE_TOOL)),
            flatFileStructure=bool(Settings.Get(Settings.FLAT_FILE_STRUCTURE)),
            numericName=bool(Settings.Get(Settings.NUMERIC_NAME)),
            clearFolder=bool(Settings.Get(Settings.CLEAR_FOLDER)),
            fileSequence=bool(Settings.Get(Settings.FILE_SEQUENCE)),
            fileSequenceDigits=Settings.Get(Settings.FILE_SEQUENCE_DIGITS),
            overwriteFiles=bool(Settings.Get(Settings.OVERWRITE_FILES)),
            rotateAAxis=bool(Settings.Get(Settings.ROTATE_A_AXIS)),
            safeYRetraction=bool(Settings.Get(Settings.SAFE_Y_RETRACTION)),
            yRetractionCoordinate=Settings.Get(Settings.Y_RETRACTION_COORDINATE),
            restoreRapidMoves=bool(Settings.Get(Settings.RESTORE_RAPID_MOVES)),
            rapidMovesMinimumDistance=20 if minimum_distance is None else minimum_distance,
            rapidMovesMaxSteps=3 if maximum_steps is None else maximum_steps,
            headerEndCodes=Settings.Get(Settings.HEADER_END_CODES) or "",
            endCodes=Settings.Get(Settings.END_CODES) or "",
        )
