from pathlib import Path
from ..settings.settings import Settings

class OperationsBody:

    def WriteBody(self, 
                  path: Path, 
                  lineNumber: int, 
                  fileName: str, 
                  fileExtension: str, 
                  *, 
                  rotationAngle: float, 
                  preserveRotation: bool) -> int:

        toolIdIndex = {}
        for operation in self._operations:
            toolId = operation.toolId
            if toolId not in toolIdIndex:
                toolIdIndex[toolId] = 0
            toolIdIndex[toolId] += 1

            if operation.hasBody:
                lineNumber = operation.WriteBody(
                    path, 
                    lineNumber, 
                    toolIdIndex[toolId], 
                    fileName, 
                    fileExtension, 
                    rotationAngle = rotationAngle, 
                    preserveRotation = preserveRotation)
                rotationAngle = None # Only apply rotation to the first operation if specified as the rotation is applied on a setup level
                preserveRotation = False # Only preserve rotation for the first operation if specified as the rotation is applied on a setup level

        if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SETUP:
            from ..programs import Programs
            
            if Settings(Settings.NUMERIC_NAME) and Programs.Current.fileName.isnumeric():
                Programs.Current.SetFileName(str(int(Programs.Current.fileName) + Settings(Settings.FILE_SEQUENCE_INTERVAL)))

        return lineNumber
