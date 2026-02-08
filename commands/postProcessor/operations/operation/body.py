import io
from pathlib import Path
from typing import Optional, TextIO, overload

from ...settings import Settings
from ...line import Line

class OperationBody(Line):
    @overload
    def WriteBody(self, fileHandler: TextIO, lineNumber: int, *, rotationAngle: Optional[float] = None, preserveRotation: Optional[bool] = False) -> int: ...

    @overload
    def WriteBody(self, folderPath: Path, lineNumber: int, fileName: str, fileExtension: str, *, rotationAngle: Optional[float] = None, preserveRotation: Optional[bool] = False) -> int: ...

    # Runtime implementation of Generate
    def WriteBody(self, fileOrPath, lineNumber: int, fileName: Optional[str] = None, fileExtension: Optional[str] = None, *, rotationAngle: Optional[float] = None, preserveRotation: Optional[bool] = False) -> int:

        # case 1: given an open file (TextIO) means that everything 
        # should be written to it and not creating a new file
        if isinstance(fileOrPath, io.TextIOBase) and fileName is None and fileExtension is None:
            fileHandler: TextIO = fileOrPath
            # first line in the output, make sure that all lines above 
            # the tool comment is written as well.

            with self._tempFilePath.open("r") as operationFile:
                line = operationFile.readline()
                row = 0
                while len(line) != 0:
                    if row >= self._bodyStartLine:
                        if row == self._bodyStartLine: # Add an extra line marking where this operation starts
                            if self._allowBlankLines:
                                fileHandler.write('\n') # keep blank line before operation start
                            lineNumber = self._writeLine(fileHandler, f"({self.name} Start)", lineNumber)
                        lineMatch = OperationBody._PARSE_LINE_RE.match(line)
                        if lineMatch:
                            if lineMatch.group("G") is not None and lineMatch.group("A") is not None:
                                gCode = lineMatch.group("G")
                                aCode = lineMatch.group("A")
                                # Special handling of A-axis rotation moves.
                                # The rotation will always be 0 as the operation
                                # are always generated one by one
                                if gCode == "0" and float(aCode) == 0.0 and row == self._rotationLine:
                                    if preserveRotation: # This is the first setup, so we want it to rotate to 0, so we keep the rotations as is
                                        pass
                                    elif rotationAngle is None: # No rotation provided, ignore the line as it will rotate to 0 which we don't want.
                                        #fileHandler.write(f" - ignored body: {line}")
                                        line = operationFile.readline()
                                        continue
                                    else: # Write our own rotation code based on the provided rotation angle
                                        lineNumber = self._writeLine(fileHandler, "(Rotating A-axis between setups)", lineNumber)
                                        # Using G53 for absolute machine coordinates for safe retraction
                                        if Settings(Settings.SAFE_Y_RETRACTION):
                                            lineNumber = self._writeLine(fileHandler, "G90 G53 G0 Z-3 Y{yRetraction}".format(yRetraction=Settings(Settings.Y_RETRACTION_COORDINATE)), lineNumber)
                                        else:
                                            lineNumber = self._writeLine(fileHandler, "G90 G53 G0 Z-3", lineNumber)
                                        lineNumber = self._writeLine(fileHandler, "G90 G54 G0 A{:.3f}".format(rotationAngle), lineNumber)

                                        #fileHandler.write(f" - ignored body: {line}")
                                        line = operationFile.readline()
                                        continue

                        lineNumber = self._write(fileHandler, line, lineNumber)
                    #else:
                        #fileHandler.write(f" - ignored body: {line}")
                    line = operationFile.readline()
                    row += 1
                    if row >= self._tailStartLine:                            
                        break
            return lineNumber

        raise TypeError("Call GenerateBody(fileHandler) or GenerateBody(folderPath, fileName, fileExtension)")