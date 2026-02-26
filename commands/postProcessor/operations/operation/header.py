from pathlib import Path
from typing import TextIO

from ...settings.settings import Settings

from .....config import PLUGIN_VERSION
from ...config import CMD_NAME
from ...file_modes import FileModes

class OperationHeader():
    def WriteHeaderStart(self, fileHandler: TextIO):
        with self._tempFilePath.open("r") as operationFile:
            
            file = Path(fileHandler.name).stem
            self._lineNumber = self._writeLine(fileHandler, "({fileName})".format(fileName = file), 0)
            self._lineNumber = self._writeLine(fileHandler, "(Generated with {pluginName} version {pluginVersion})".format(pluginName = CMD_NAME, pluginVersion = PLUGIN_VERSION), self._lineNumber)
            if Settings(Settings.RESTORE_RAPID_MOVES):
                self._lineNumber = self._writeLine(fileHandler, "(Restore rapid moves enabled: {restoreRapidMoves}, maximum steps inbetween start and stop: {maximumSteps}, minimum travel distance: {minimumDistance}mm)".format(
                    restoreRapidMoves = Settings(Settings.RESTORE_RAPID_MOVES),
                    maximumSteps = Settings(Settings.RAPID_MOVES_MAX_STEPS),
                    minimumDistance = Settings(Settings.RAPID_MOVES_MINIMUM_DISTANCE)
                ), self._lineNumber)
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
                    break
                self._lineNumber = self._write(fileHandler, line, self._lineNumber)
                line = operationFile.readline()
                row += 1

    def WriteToolComment(self, fileHandler: TextIO):
        with self._tempFilePath.open(FileModes.READ) as operationFile:
            line = operationFile.readline()
            row = 0
            while len(line) != 0:
                if row == self._toolCommentLine:
                    self._lineNumber = self._write(fileHandler, line, self._lineNumber)
                    break
                line = operationFile.readline()
                row += 1

    def WriteHeaderEnd(self, fileHandler: TextIO):
        with self._tempFilePath.open(FileModes.READ) as operationFile:
            line = operationFile.readline()
            row = 0
            while len(line) != 0:
                if row > self._toolCommentLine and row <= self._headerEndLine:
                    self._lineNumber = self._write(fileHandler, line, self._lineNumber)
                line = operationFile.readline()
                row += 1

    def WriteHeader(self, fileHandler: TextIO):
        self.WriteHeaderStart(fileHandler)
        self.WriteToolComment(fileHandler)
        self.WriteHeaderEnd(fileHandler)

