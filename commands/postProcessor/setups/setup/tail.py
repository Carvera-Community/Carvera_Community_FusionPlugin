from pathlib import Path

from ...settings.settings import Settings

class SetupTail:
    @property
    def hasTail(self):
        return self._operations is not None and self._operations.hasTail
    
    def WriteTail(self, folderPath: Path, lineNumber: int, fileName: str, fileExtension: str) -> int:

        if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SINGLE_FILE:
             firstTailOperation = next((operation for operation in self._operations if operation.hasTail), None)
             return lineNumber if firstTailOperation is None else firstTailOperation.WriteTail(folderPath, lineNumber, 1, fileName, fileExtension)

        return lineNumber if not self.hasTail else self._operations.WriteTail(folderPath, lineNumber, self._getFileName(fileName), fileExtension)
