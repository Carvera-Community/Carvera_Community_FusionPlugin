from pathlib import Path
from typing import Optional, TextIO

from ..file_modes import FileModes

class OperationsHeader:
    @property
    def hasHeader(self):
        return self._operationWithHeader is not None

    def WriteFirstHeaderStart(self, path: Path, fileName: str, fileExtension: str) -> int:
        if len(self._operations) == 0:
            return 0
        
        # Always OVERWRITE on first header as it indcates a new file
        with self._getFileHandler(path, FileModes.OVERWRITE, fileName, self._operations[0], 1, fileExtension) as fileHandler:
            return self._operations[0].WriteHeaderStart(fileHandler) # New file, so line number starts at 0

    def WriteToolComments(self, path: Path, lineNumber: int, fileName: str, fileExtension: str) -> int:
        if len(self._operations) == 0:
            return lineNumber

        toolIdIndex = {}
        fileHandler: Optional[TextIO] = None

        for operation in self._operations:
            toolId = operation.toolId
            if toolId not in toolIdIndex:
                toolIdIndex[toolId] = 0
            toolIdIndex[toolId] += 1
            try: 
                with self._getFileHandler(path, FileModes.APPEND, fileName, operation, toolIdIndex[toolId], fileExtension) as fileHandler:
                    lineNumber = operation.WriteToolComment(fileHandler, lineNumber)
            finally:
                if fileHandler is not None and not fileHandler.closed:
                    fileHandler.close()
        return lineNumber

    def WriteFirstHeaderEnd(self, path: Path, lineNumber: int, fileName: str, fileExtension: str) -> int:
        if len(self._operations) == 0:
            return lineNumber

        with self._getFileHandler(path, FileModes.APPEND, fileName, self._operations[0], 1, fileExtension) as fileHandler:
            return self._operations[0].WriteHeaderEnd(fileHandler, lineNumber)

    def WriteHeader(self, path: Path, fileName: str, fileExtension: str) -> int:

        if len(self._operations) == 0:
            return 0

        toolIdIndex = {}
        for operation in self._operations:
            toolId = operation.toolId
            if toolId not in toolIdIndex:
                toolIdIndex[toolId] = 0
            toolIdIndex[toolId] += 1
            lineNumber = operation.WriteHeader(path, fileName, toolIdIndex[toolId], fileExtension)
        return lineNumber
