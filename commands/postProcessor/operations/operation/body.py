from typing import Optional, TextIO

from ...file_modes import FileModes
from ...settings.settings import Settings
from ...line import Line

class OperationBody(Line):
    def WriteBody(self, fileHandler: TextIO, rotationAngle: Optional[float] = None, preserveRotation: Optional[bool] = False):
        with self._tempFilePath.open(FileModes.READ) as operationFile:
            line = operationFile.readline()
            row = 0
            rapidsEnds = 0
            readNextLine = False
            while len(line) != 0:
                if readNextLine:
                    line = operationFile.readline() 
                    row += 1
                    readNextLine = False

                if row >= self._bodyStartLine:
                    if row == self._bodyStartLine: # Add an extra line marking where this operation starts
                        if self._allowBlankLines:
                            fileHandler.write('\n') # keep blank line before operation start
                        self._lineNumber = self._writeLine(fileHandler, f"({self.name})", self._lineNumber)
                    if row + 1 in self._rapidsAnalysis: # Add rapids comments if this line is the start of a rapid move
                        rapidsEnds = self._rapidsAnalysis[row + 1]
                        lineMatch = OperationBody._PARSE_LINE_RE.match(line)
                        if lineMatch:
                            if lineMatch.group("G") is not None:
                                if int(lineMatch.group("G")) == 1:
                                    gStart, gEnd = lineMatch.span("G")
                                    line = (line[:gStart] + "0" + line[gEnd:]).rstrip() + " (Rapid movement start)\n" # Change G1 to G0 for rapid move comment line
                            else:
                                self._lineNumber = self._writeLine(fileHandler, f"G0 {line.rstrip()} (Rapid movement start)", self._lineNumber)
                                readNextLine = True
                                continue
                    if row + 1 == rapidsEnds:
                        rapidsEnds = 0
                        self._lineNumber = self._write(fileHandler, line, self._lineNumber)
                        line = "G1 (Rapid movement end)\n" # Add a line after the rapid move to switch back to G1 if it was changed for the rapid move comment
                    if self._matchLine(fileHandler, line, row, rotationAngle, preserveRotation):
                        readNextLine = True
                        continue

                    self._lineNumber = self._write(fileHandler, line, self._lineNumber)

                line = operationFile.readline()
                row += 1
                if row >= self._tailStartLine:                            
                    break

    def _matchLine(self, fileHandler: TextIO, line: str, row: int, rotationAngle: Optional[float], preserveRotation: Optional[bool] = False) -> bool:
        lineMatch = OperationBody._PARSE_LINE_RE.match(line)
        if lineMatch:
            if lineMatch.group("G") is not None and lineMatch.group("A") is not None:
                gCode = lineMatch.group("G")
                aCode = lineMatch.group("A")
                if gCode == "0" and float(aCode) == 0.0 and row == self._rotationLine:
                    # Special handling of A-axis rotation moves.
                    # The rotation will always be 0 as the operation
                    # are always generated one by one
                    if self._handleRotation(fileHandler, rotationAngle, preserveRotation):
                        return True
        return False

    def _handleRotation(self, fileHandler: TextIO, rotationAngle: Optional[float], preserveRotation: Optional[bool] = False) -> bool:
        if preserveRotation: # This is the first setup, so we want it to rotate to 0, so we keep the rotation line as is
            return False
        elif rotationAngle is None: # No rotation provided, ignore the line as it will rotate to 0 which we don't want.
            return True
        else: # Write our own rotation code based on the provided rotation angle
            self._lineNumber = self._writeLine(fileHandler, "(Rotating A-axis between setups)", self._lineNumber)
            # Using G53 for absolute machine coordinates for safe retraction
            if Settings(Settings.SAFE_Y_RETRACTION):
                self._lineNumber = self._writeLine(fileHandler, "G90 G53 G0 Z-3 Y{yRetraction}".format(yRetraction = Settings(Settings.Y_RETRACTION_COORDINATE)), self._lineNumber)
            else:
                self._lineNumber = self._writeLine(fileHandler, "G90 G53 G0 Z-3", self._lineNumber)
            self._lineNumber = self._writeLine(fileHandler, "G90 G54 G0 A{angle}".format(angle = f"{rotationAngle:.3f}".rstrip("0").rstrip(".")), self._lineNumber)
            return True