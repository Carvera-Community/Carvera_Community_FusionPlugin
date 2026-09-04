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
        minimum_distance = Settings.get(Settings.RAPID_MOVES_MINIMUM_DISTANCE)
        maximum_steps = Settings.get(Settings.RAPID_MOVES_MAX_STEPS)
        return cls(
            operationsGrouping=Settings.get(Settings.OPERATIONS_GROUPING),
            combineTool=bool(Settings.get(Settings.COMBINE_TOOL)),
            flatFileStructure=bool(Settings.get(Settings.FLAT_FILE_STRUCTURE)),
            numericName=bool(Settings.get(Settings.NUMERIC_NAME)),
            clearFolder=bool(Settings.get(Settings.CLEAR_FOLDER)),
            fileSequence=bool(Settings.get(Settings.FILE_SEQUENCE)),
            fileSequenceDigits=Settings.get(Settings.FILE_SEQUENCE_DIGITS),
            overwriteFiles=bool(Settings.get(Settings.OVERWRITE_FILES)),
            rotateAAxis=bool(Settings.get(Settings.ROTATE_A_AXIS)),
            safeYRetraction=bool(Settings.get(Settings.SAFE_Y_RETRACTION)),
            yRetractionCoordinate=Settings.get(Settings.Y_RETRACTION_COORDINATE),
            restoreRapidMoves=bool(Settings.get(Settings.RESTORE_RAPID_MOVES)),
            rapidMovesMinimumDistance=20 if minimum_distance is None else minimum_distance,
            rapidMovesMaxSteps=3 if maximum_steps is None else maximum_steps,
            headerEndCodes=Settings.get(Settings.HEADER_END_CODES) or "",
            endCodes=Settings.get(Settings.END_CODES) or "",
        )
