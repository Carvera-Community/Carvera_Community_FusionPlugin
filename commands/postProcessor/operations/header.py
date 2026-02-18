from pathlib import Path
from typing import Optional, TextIO

from ..settings.settings import Settings
from ..file_modes import FileModes
from .operation.operation import Operation

class OperationsHeader:
    @property
    def hasHeader(self):
        return self._operationWithHeader is not None

    def WriteFirstHeaderStart(self) -> None:
        # SINGLE_FILE, SETUP
        if len(self._operations) != 0:
            pathToOpen: Path = self._path / f"{self._fileName}{self._fileExtension}"

            if pathToOpen.exists() and not Settings(Settings.OVERWRITE_FILES):
                raise FileExistsError(f"File {pathToOpen} already exists and overwrite is not allowed.")
            # Always OVERWRITE on first header as it indcates a new file
            with pathToOpen.open(FileModes.OVERWRITE) as fileHandler:
                self._operations[0].WriteHeaderStart(fileHandler)
                self._lineNumber = self._operations[0].lineNumber

    def WriteToolComments(self) -> None:
        # SINGLE_FILE, SETUP
        if len(self._operations) == 0:
            return

        toolIdIndex = {}
        fileHandler: Optional[TextIO] = None

        for operation in self._operations:
            toolId = operation.toolId
            if toolId not in toolIdIndex:
                toolIdIndex[toolId] = 0
            toolIdIndex[toolId] += 1

            pathToOpen: Path = self._path / f"{self._fileName}{self._fileExtension}"
            with pathToOpen.open(FileModes.APPEND) as fileHandler:
                operation.SetLineNumber(self._lineNumber)
                operation.WriteToolComment(fileHandler)
                self._lineNumber = operation.lineNumber

    def WriteFirstHeaderEnd(self) -> None:
        # SINGLE_FILE, SETUP
        if len(self._operations) != 0:
            pathToOpen: Path = self._path / f"{self._fileName}{self._fileExtension}"
            with pathToOpen.open(FileModes.APPEND) as fileHandler:
                self._operations[0].SetLineNumber(self._lineNumber)
                self._operations[0].WriteHeaderEnd(fileHandler)
                self._lineNumber = self._operations[0].lineNumber

    def WriteHeader(self) -> None:
        # SETUP_AND_TOOL, PER_OPERATION
        if len(self._operations) == 0:
            return

        previousTool = None
        toolIdIndex = {}
        operation: Operation
        for operation in self:
            toolId = operation.toolId
            if toolId not in toolIdIndex:
                toolIdIndex[toolId] = 0
            toolIdIndex[toolId] += 1

            self._setOperationFileName(operation, toolIdIndex[toolId])

            pathToOpen: Path = self._path / f"{operation.fileName}{self._fileExtension}"
            if pathToOpen.exists() and not Settings(Settings.OVERWRITE_FILES):
                raise FileExistsError(f"File {pathToOpen} already exists and overwrite is not allowed.")
            with pathToOpen.open(FileModes.OVERWRITE) as fileHandler:
                if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.PER_OPERATION:
                    operation.SetLineNumber(0)
                    operation.WriteHeaderStart(fileHandler)
                    operation.WriteToolComment(fileHandler)
                    operation.WriteHeaderEnd(fileHandler)
                    self._lineNumber = operation.lineNumber
                else: # SETUP_AND_TOOL
                    toolChange = previousTool is None or previousTool != toolId
                    if toolChange: # New tool, new header
                        operation.SetLineNumber(0)
                        operation.WriteHeaderStart(fileHandler)
                    
                    operation.WriteToolComment(fileHandler)

                    if toolChange:
                        operation.WriteHeaderEnd(fileHandler)
            previousTool = toolId            
