from pathlib import Path
from typing import TextIO

from .....config import PLUGIN_VERSION
from ...config import CMD_NAME
from ...file_modes import FileModes

class OperationHeader():
    def WriteHeaderStart(self, fileHandler: TextIO) -> int:
        with self._tempFilePath.open("r") as operationFile:
            
            file = Path(fileHandler.name).stem
            lineNumber = self._writeLine(fileHandler, "({fileName})".format(fileName = file), 0)
            lineNumber = self._writeLine(fileHandler, "(Generated with {pluginName} version {pluginVersion})".format(pluginName = CMD_NAME, pluginVersion = PLUGIN_VERSION), lineNumber)

            line = operationFile.readline()
            row = 0

            while len(line) != 0:
                # It's the temporary file name, so ignore it as the 
                # real name will be written later
                if line == f"({self._tempFilePath.stem})\n": 
                    line = operationFile.readline()
                    row += 1
                    continue
                elif row == self._toolCommentLine:
                    return lineNumber
                lineNumber = self._write(fileHandler, line, lineNumber)
                line = operationFile.readline()
                row += 1

        return lineNumber

    def WriteToolComment(self, fileHandler: TextIO, lineNumber: int) -> int:
        with self._tempFilePath.open(FileModes.READ) as operationFile:
            line = operationFile.readline()
            row = 0
            while len(line) != 0:
                if row == self._toolCommentLine:
                    lineNumber = self._write(fileHandler, line, lineNumber)
                    return lineNumber
                line = operationFile.readline()
                row += 1

        return lineNumber

    def WriteHeaderEnd(self, fileHandler: TextIO, lineNumber: int) -> int:
        with self._tempFilePath.open(FileModes.READ) as operationFile:
            line = operationFile.readline()
            row = 0
            while len(line) != 0:
                if row > self._toolCommentLine and row <= self._headerEndLine:
                    lineNumber = self._write(fileHandler, line, lineNumber)
                line = operationFile.readline()
                row += 1

        # For numeric names
        from ...programs import Programs
        from ...settings.settings import Settings
        
        if Settings(Settings.NUMERIC_NAME) and Programs.Current.fileName.isnumeric():
            Programs.Current.SetFileName(str(int(Programs.Current.fileName) + Settings(Settings.FILE_SEQUENCE_INTERVAL)))
        return lineNumber
    
    def WriteHeader(self, path, fileName, toolIdIndex, fileExtension) -> int:
        try: 
            with self._getFileHandler(path, FileModes.OVERWRITE, fileName, toolIdIndex, fileExtension) as fileHandler:
                lineNumber = self.WriteHeaderStart(fileHandler)
                lineNumber = self.WriteToolComment(fileHandler, lineNumber)
                return self.WriteHeaderEnd(fileHandler, lineNumber)
        finally:
            if fileHandler is not None:
                fileHandler.close()

