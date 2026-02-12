from pathlib import Path

class SetupBody:

    def WriteBody(self, 
                  path: Path, 
                  lineNumber: int, 
                  fileName: str, 
                  fileExtension: str, 
                  *, 
                  rotationAngle: float, 
                  preserveRotation: bool
    ) -> int:
        return self._operations.WriteBody(
            path, 
            lineNumber, 
            self._getFileName(fileName), 
            fileExtension, 
            rotationAngle = rotationAngle, 
            preserveRotation = preserveRotation
        )
