from pathlib import Path
from ..settings.settings import Settings

class OperationsTail:
    @property
    def hasTail(self):
        return self._operationWithTail is not None

    def WriteTail(self, folderPath: Path, lineNumber: int, fileName: str, fileExtension: str) -> int:
        if self._operationWithTail is None:
            return lineNumber

        if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SETUP:
            firstTailOperation = next((operation for operation in self._operations if operation.hasTail), None)
            if firstTailOperation is not None:
                return firstTailOperation.WriteTail(folderPath, lineNumber, 1, fileName, fileExtension)
            return lineNumber

        toolIdIndex = {}
        for operation in self._operations:
            toolId = operation.toolId
            if toolId not in toolIdIndex:
                toolIdIndex[toolId] = 0
            toolIdIndex[toolId] += 1

            lineNumber = operation.WriteTail(folderPath, lineNumber, toolIdIndex[toolId], fileName, fileExtension)
        return lineNumber
