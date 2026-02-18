from ..file_modes import FileModes
from ..settings.settings import Settings

from .operation.operation import Operation

class OperationsTail:
    @property
    def hasTail(self):
        return self._operationWithTail is not None

    def WriteFirstTail(self) -> None:
        with (self._path / f"{self._fileName}{self._fileExtension}").open(FileModes.APPEND) as fileHandler:
            self._operationWithTail.SetLineNumber(self._lineNumber)
            self._operationWithTail.WriteTail(fileHandler)
        if Settings(Settings.NUMERIC_NAME):
            self._fileName = str(int(self._fileName) + Settings(Settings.FILE_SEQUENCE_INTERVAL)).rjust(Settings(Settings.FILE_SEQUENCE_DIGITS), '0')

    def WriteTail(self):
        # SETUP_AND_TOOL, PER_OPERATION
        if self._operationWithTail is None:
            return 

        toolIdIndex = {}
        #firstOperationPerTool: dict[int, Operation] = {}
        operation: Operation
        for operation in self:
            toolId = operation.toolId
            if toolId not in toolIdIndex:
                toolIdIndex[toolId] = 0
            toolIdIndex[toolId] += 1

            self._setOperationFileName(operation, toolIdIndex[toolId])

            with (self._path / f"{operation.fileName}{self._fileExtension}").open(FileModes.APPEND) as fileHandler:
                operation.WriteTail(fileHandler)
