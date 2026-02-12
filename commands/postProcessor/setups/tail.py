from pathlib import Path
from typing import Optional

from ..settings.settings import Settings

class SetupsTail():
    @classmethod
    def WriteTail(cls, folderPath: Path, lineNumber: int, fileName: Optional[str] = None, fileExtension: Optional[str] = None):

        if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SINGLE_FILE:
             firstTailSetup = next((setup for setup in cls.selected if setup.hasTail), None)
             return lineNumber if firstTailSetup is None else firstTailSetup.WriteTail(folderPath, lineNumber, fileName, fileExtension)

        for setup in cls.selected:
            lineNumber = setup.WriteTail(folderPath, lineNumber, fileName, fileExtension)
        return lineNumber
