import io
from pathlib import Path
from typing import Optional, TextIO, overload


class OperationHeader():
    # Crude implementation, optimally it should be one file open
    # and iterate over it. Room for improvement.
    def WriteHeaderStart(self, fileHandler: TextIO, addLineNumbers: bool, lineNumber: int, digits: int) -> int:
        with self._tempFilePath.open("r") as operationFile:
            
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
                lineNumber = self._write(fileHandler, line, lineNumber, addLineNumbers, digits)
                line = operationFile.readline()
                row += 1

        return lineNumber

    def WriteToolComment(self, fileHandler: TextIO, addLineNumbers: bool, lineNumber: int, digits: int) -> int:
        with self._tempFilePath.open("r") as operationFile:
            line = operationFile.readline()
            row = 0
            while len(line) != 0:
                if row == self._toolCommentLine:
                    lineNumber = self._write(fileHandler, line, lineNumber, addLineNumbers, digits)
                    return lineNumber
                line = operationFile.readline()
                row += 1

        return lineNumber

    def WriteHeaderEnd(self, fileHandler: TextIO, addLineNumbers: bool, lineNumber: int, digits: int) -> int:
        with self._tempFilePath.open("r") as operationFile:
            line = operationFile.readline()
            row = 0
            while len(line) != 0:
                if row > self._toolCommentLine and row <= self._headerEndLine:
                    lineNumber = self._write(fileHandler, line, lineNumber, addLineNumbers, digits)
                line = operationFile.readline()
                row += 1

        return lineNumber

    # Type signatures for tools (mypy/IDE) hints

    # If GenerateHeader is called with a fileHandler it means that the output
    # will only be one file
    @overload
    def WriteHeader(self, fileHandler: TextIO, lineNumber: int, addLineNumbers: bool, digits: int, briefHeader: bool) -> int: ...

    # If GenerateHeader is called with folder it means that 
    # multiple files will be generated on lower levels of the hierarchy
    @overload
    def WriteHeader(self, folderPath: Path, lineNumber: int, addLineNumbers: bool, digits: int, briefHeader: bool, fileName: str, fileExtension: str) -> int: ...

    # Runtime implementation of Generate
    def WriteHeader(self, pathOrFile, lineNumber: int, addLineNumbers: bool, digits: int, briefHeader: bool, fileName: Optional[str] = None, fileExtension: Optional[str] = None) -> int:

        fileOpened = False
        # If given a Path, create the folder structure and the file to write to
        try:
            if isinstance(pathOrFile, Path):
                folder: Path = pathOrFile
                folder.mkdir(parents=True, exist_ok=True)
                filename = f"{fileName}{fileExtension}"
                headerFile = folder / filename
                fileHandler = headerFile.open("w", encoding="utf-8")
                fileOpened = True

            if isinstance(pathOrFile, io.TextIOBase):
                fileHandler: TextIO = pathOrFile

            if not briefHeader:
                self.WriteHeaderStart(fileHandler, addLineNumbers, lineNumber, digits)
            self.WriteToolComment(fileHandler, addLineNumbers, lineNumber, digits)
            if not briefHeader:
                self.WriteHeaderEnd(fileHandler, addLineNumbers, lineNumber, digits)
            self._headerGenerated = True
            return lineNumber

        finally:
            if fileOpened:
                fileHandler.close()                
