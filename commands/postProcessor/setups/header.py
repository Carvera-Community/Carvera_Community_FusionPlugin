from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..settings.settings import Settings
from ..line import Line

class SetupsHeader(Line):
    @classmethod
    def WriteHeader(cls, folderPath: Path, lineNumber: int, fileName: Optional[str] = None, fileExtension: Optional[str] = None) -> int:


        if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SINGLE_FILE:
            firstSetup = next((setup for setup in cls.selected if setup.hasHeader), None)

            if firstSetup is None: 
                return lineNumber
            
            lineNumber = firstSetup.WriteHeaderStart(folderPath, fileName, fileExtension)
            for setup in cls.selected:
                lineNumber = setup.WriteToolComments(folderPath, lineNumber, fileName, fileExtension)
            return firstSetup.WriteHeaderEnd(folderPath, lineNumber, fileName, fileExtension)

        for setup in cls.selected:
            lineNumber = setup.WriteHeader(folderPath, fileName, fileExtension)
        return lineNumber
