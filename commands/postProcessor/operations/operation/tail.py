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
                        lineNumber = self._writeLine(fileHandler, f"({self.name})", lineNumber)
                    if row >= self._tailStartLine:
                        lineNumber = self._write(fileHandler, line, lineNumber)
                    line = operationFile.readline()
                    row += 1
            # For numeric file names
            from ...programs import Programs
            from ...settings.settings import Settings

            if Settings(Settings.NUMERIC_NAME) and Programs.Current.fileName.isnumeric():
                Programs.Current.SetFileName(str(int(Programs.Current.fileName) + Settings(Settings.FILE_SEQUENCE_INTERVAL)))
            return lineNumber

        finally:
            if fileHandler is not None and not fileHandler.closed:
                fileHandler.close()
        
    #endregion