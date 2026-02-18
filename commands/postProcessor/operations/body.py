from pathlib import Path
from ..settings.settings import Settings
from ..file_modes import FileModes

from .operation.operation import Operation

class OperationsBody:

    def WriteBody(self, rotationAngle: float, preserveRotation: bool):

        toolIdIndex = {}
        operation: Operation
        for operation in [op for op in self._operations if op.hasBody]:
            toolId = operation.toolId
            if toolId not in toolIdIndex:
                toolIdIndex[toolId] = 0
            toolIdIndex[toolId] += 1

            self._setOperationFileName(operation, toolIdIndex[toolId])

            pathToOpen: Path = self._path / f"{operation.fileName}{self._fileExtension}"
            with pathToOpen.open(FileModes.APPEND) as fileHandler:
                if Settings(Settings.OPERATIONS_GROUPING) in [Settings.OperationsGroupings.SINGLE_FILE, 
                                                                Settings.OperationsGroupings.SETUP]:
                    # Line number is saved in the setup (operations) when writing the header, so it can be used here
                    operation.SetLineNumber(self._lineNumber)
                
                operation.WriteBody(fileHandler, rotationAngle, preserveRotation)
                self._lineNumber = operation.lineNumber

                rotationAngle = None # Only apply rotation to the first operation if specified as the rotation is applied on a setup level
                preserveRotation = False # Only preserve rotation for the first operation if specified as the rotation is applied on a setup level
