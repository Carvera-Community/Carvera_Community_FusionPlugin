from pathlib import Path
from typing import Optional

from ...settings.settings import Settings

from ...line import Line

class SetupHeader(Line):
    @property
    def hasHeader(self):
        return self._operations is not None and self._operations.hasHeader

    def WriteHeaderStart(self, path: Path, fileName: str, fileExtension: str) -> int:
        return self._operations.WriteFirstHeaderStart(path, self._getFileName(fileName), fileExtension)
    
    def WriteToolComments(self, path: Path, lineNumber: int, fileName: str, fileExtension: str) -> int: 
        return self._operations.WriteToolComments(path, lineNumber, self._getFileName(fileName), fileExtension) 
    
    def WriteHeaderEnd(self, path: Path, lineNumber: int, fileName: str, fileExtension: str) -> int:
        return self._operations.WriteFirstHeaderEnd(path, lineNumber, self._getFileName(fileName), fileExtension)

    def WriteHeader(self, path: Path, fileName: str, fileExtension: str) -> int:

        if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SETUP:
            lineNumber = self.WriteHeaderStart(path, fileName, fileExtension)
            lineNumber = self.WriteToolComments(path, lineNumber, fileName, fileExtension)
            return self.WriteHeaderEnd(path, lineNumber, fileName, fileExtension)

        return self._operations.WriteHeader(path, self._getFileName(fileName), fileExtension)


