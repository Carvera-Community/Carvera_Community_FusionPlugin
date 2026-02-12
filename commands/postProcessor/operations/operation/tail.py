from pathlib import Path
from typing import Optional, TextIO

from ...file_modes import FileModes

class OperationTail():

    def WriteTail(self, folderPath: Path, lineNumber: int, toolIdIndex: int, fileName: str, fileExtension: str) -> int:
        fileHandler: Optional[TextIO] = None

        try:
            fileHandler: TextIO = self._getFileHandler(folderPath, FileModes.APPEND, fileName, toolIdIndex, fileExtension)

            with self._tempFilePath.open(FileModes.READ) as operationFile:
                line = operationFile.readline()
                row = 0
                while len(line) != 0:
                    if row == self._tailStartLine: # Add an extra line marking where this operation tail starts
                        if(self._allowBlankLines):
                            fileHandler.write("\n") # ensure blank line before operation tail
                        lineNumber = self._writeLine(fileHandler, f"({self.name} Tail)", lineNumber)
                    if row >= self._tailStartLine:
                        lineNumber = self._write(fileHandler, line, lineNumber)
                    line = operationFile.readline()
                    row += 1
            return lineNumber

        finally:
            if fileHandler is not None:
                fileHandler.close()
        
    #endregion