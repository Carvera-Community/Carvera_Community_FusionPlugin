import io
from pathlib import Path
from typing import Optional, TextIO, overload

class OperationTail():

    #region GenerateTail
    # Type signatures for tools (mypy/IDE) hints

    # If GenerateTail is called with a fileHandler it means that the output
    # will only be one file
    @overload
    def WriteTail(self, fileHandler: TextIO, lineNumber: int, addLineNumbers: bool, digits: int) -> int: ...

    # If GenerateTail is called with folder it means that 
    # multiple files will be generated on lower levels of the hierarchy
    @overload
    def WriteTail(self, folderPath: Path, lineNumber: int, addLineNumbers: bool, digits: int, fileName: str, fileExtension: str) -> int: ...

    # Runtime implementation of Generate
    def WriteTail(self, arg, lineNumber: int, addLineNumbers: Optional[bool] = None, digits: Optional[int] = None, fileName: Optional[str] = None, fileExtension: Optional[str] = None) -> int:

        # case 1: given an open file (TextIO) means that everything 
        # should be written to it and not creating a new file
        if isinstance(arg, io.TextIOBase) and fileName is None and fileExtension is None:
            fileHandler: TextIO = arg
            with self._tempFilePath.open("r") as operationFile:
                line = operationFile.readline()
                row = 0
                while len(line) != 0:
                    if row == self._tailStartLine: # Add an extra line marking where this operation tail starts
                        if(self._allowBlankLines):
                            fileHandler.write("\n") # ensure blank line before operation tail
                        lineNumber = self._writeLine(fileHandler, f"({self.name} Tail)", lineNumber, addLineNumbers, digits)
                    if row >= self._tailStartLine:
                        lineNumber = self._write(fileHandler, line, lineNumber, addLineNumbers, digits)
                    line = operationFile.readline()
                    row += 1
            return lineNumber

        raise TypeError("Call GenerateTail(fileHandler) or GenerateTail(folderPath, fileName, fileExtension)")
    #endregion