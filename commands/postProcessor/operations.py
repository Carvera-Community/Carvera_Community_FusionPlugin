import io
from pathlib import Path
from typing import List, List, Optional, TextIO, overload
from .settings import Settings
from .operation import Operation


class Operations:
    def __init__(self, operations):
        self._outputFileName: str = None
        self._operations = list[Operation]()
        self._operationWithTail: Operation = None
        self._singleFile: bool = None
        self._headerGenerated = False

        i = 0
        operation = None
        while i < len(operations):
            if(operations[i].isSuppressed):
                i += 1
                continue
            # Look ahead for operations without a toolpath. This can happen
            # with a manual operation. Group it with current operation.
            # Or if first, group it with subsequent ones.
            # Also optionally group together operations with the same tool number

            operation = Operation()
            operation.Append(operations[i], operations[i].hasToolpath) # add first operation
            i += 1
            while i < len(operations):
                if(operations[i].isSuppressed):
                    i += 1
                    continue
                # Append to current group if:
                # - operation has no toolpath, or
                # - current group has no tool yet (we haven't encountered a toolpath), or
                # - we're combining tools and this op uses the same tool as the group
                # otherwise finish current group and start a new one
                if (not operations[i].hasToolpath) \
                    or (not operation.hasTool) \
                    or (Settings.Get(Settings.COMBINE_TOOL) \
                        and Operations.GetToolNumber(operations[i]) == operation.toolId):
                    operation.Append(operations[i], operations[i].hasToolpath)
                    i += 1
                else:
                    # different tool (or not combining) -> finish current group
                    self._operations.append(operation)
                    break
        if operation is not None: # append final group
            self._operations.append(operation)
                
    def SetOutputFolder(self, folder):
        self._outputFolder = folder

    @staticmethod
    def GetToolNumber(operation):
        return operation.tool.parameters.itemByName("tool_number").value.value

    def Process(self, tmpPath: Path):
        for operation in self._operations:
            operation.Process(tmpPath)

    def SetOutputFileName(self, fileName):
        self._outputFileName = fileName

    @property
    def hasTail(self):
        return self._operationWithTail is not None

    @property
    def headerGenerated(self):
        return self._headerGenerated

    # Type signatures for tools (mypy/IDE) hints

    # If GenerateHeader is called with a fileHandler it means that the output
    # will only be one file
    @overload
    def GenerateHeader(self, fileHandler: TextIO, lineNumber: int, addLineNumbers: bool, digits: int, briefHeader: bool) -> int: ...

    # If GenerateHeader is called with folder + name + ext it means that 
    # multiple files will be generated on lower levels of the hierarchy
    @overload
    def GenerateHeader(self, folderPath: Path, lineNumber: int, addLineNumbers: bool, digits: int, briefHeader: bool, fileName: str, fileExtension: str) -> int: ...

    # Runtime implementation of GenerateHeader
    def GenerateHeader(self, arg, lineNumber: int, addLineNumbers: bool, digits: bool, briefHeader: bool, fileName: Optional[str] = None, fileExtension: Optional[str] = None) -> int:

        self._headerGenerated = briefHeader

        # case 1: given an open file (TextIO) means that everything 
        # should be written to it and no directory structure
        # should be created.
        if isinstance(arg, io.TextIOBase) and fileName is None and fileExtension is None:
            fileHandler: TextIO = arg
            if self._singleFile is None:
                self._singleFile = Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SINGLE_FILE

            for operation in self._operations:
                if self._singleFile:
                    lineNumber = operation.GenerateHeader(fileHandler, lineNumber, addLineNumbers, digits, self._headerGenerated)
                    if not self._headerGenerated: self._headerGenerated = operation.headerGenerated
                    if operation.hasTail: self._operationWithTail = operation # Just keep the last operation with a tail to end the whole file
                else: # This is not done yet...
                    pass
            return lineNumber
                
        # case 2: given folder + name + ext
        if isinstance(arg, Path) and fileName is not None and fileExtension is not None:
            folder: Path = arg
            folder.mkdir(parents=True, exist_ok=True)
            filename = f"{fileName}{fileExtension}"
            p = folder / filename
            # öppna och skriv via samma inre funktion
            with p.open("w", encoding="utf-8") as fh:
                self._generate_to_file(fh, addLineNumbers, digits)
            return p

        raise TypeError("Call GenerateHeader(fileHandler) or GenerateHeader(folderPath, fileName, fileExtension)")

    # Type signatures for tools (mypy/IDE) hints

    # If GenerateBody is called with a fileHandler it means that the output
    # will only be one file
    @overload
    def GenerateBody(self, fileHandler: TextIO, lineNumber: int, addLineNumbers: bool, digits: int, removeARotations: bool) -> int: ...

    # If GenerateBody is called with folder + name + ext it means that 
    # multiple files will be generated on lower levels of the hierarchy
    @overload
    def GenerateBody(self, folderPath: Path, lineNumber: int, addLineNumbers: bool, digits: int, removeARotations: bool, fileName: str, fileExtension: str) -> int: ...

    # Runtime implementation of GenerateBody
    def GenerateBody(self, arg, lineNumber: int, addLineNumbers: bool, digits: int, removeARotations: bool, fileName: Optional[str] = None, fileExtension: Optional[str] = None) -> int:

        if self._singleFile is None:
            self._singleFile = Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SINGLE_FILE
        # case 1: given an open file (TextIO) means that everything 
        # should be written to it and no directory structure
        # should be created.
        toolComments = []

        if isinstance(arg, io.TextIOBase) and fileName is None and fileExtension is None:
            fileHandler: TextIO = arg
            i = 0
            for operation in self._operations:
                if self._singleFile:  
                    if operation.hasBody:
                        lineNumber = operation.GenerateBody(fileHandler, lineNumber, addLineNumbers, digits, removeARotations)
                    if operation.hasTail:
                        # Just keep the last operation with a tail to 
                        # end the whole file
                        self._operationWithTail = operation 
                    i += 1
                else: # This is not done yet...
                    pass
            return lineNumber
                
        # case 2: given folder + name + ext
        if isinstance(arg, Path) and fileName is not None and fileExtension is not None:
            folder: Path = arg
            folder.mkdir(parents=True, exist_ok=True)
            filename = f"{fileName}{fileExtension}"
            p = folder / filename
            # öppna och skriv via samma inre funktion
            with p.open("w", encoding="utf-8") as fh:
                self._generate_to_file(fh)
            return p

        raise TypeError("Call GenerateBody(fileHandler) or GenerateBody(folderPath, fileName, fileExtension)")

    # Type signatures for tools (mypy/IDE) hints

    # If GenerateTail is called with a fileHandler it means that the output
    # will only be one file
    @overload
    def GenerateTail(self, fileHandler: TextIO, addLineNumbers: bool, digits: int) -> int: ...

    # If GenerateTail is called with folder + name + ext it means that 
    # multiple files will be generated on lower levels of the hierarchy
    @overload
    def GenerateTail(self, folderPath: Path, addLineNumbers: bool, digits: int, fileName: str, fileExtension: str) -> int: ...

    # Runtime implementation of GenerateTail
    def GenerateTail(self, arg, lineNumber: int, addLineNumbers: Optional[bool] = None, digits: Optional[int] = None, fileName: Optional[str] = None, fileExtension: Optional[str] = None) -> int:

        if self._operationWithTail is None:
            return lineNumber

        # case 1: given an open file (TextIO) means that everything 
        # should be written to it and no directory structure
        # should be created.
        toolComments = []

        if isinstance(arg, io.TextIOBase) and fileName is None and fileExtension is None:
            fileHandler: TextIO = arg
            if self._singleFile is None:
                self._singleFile = Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SINGLE_FILE

            if self._singleFile:  
                # Attach the tail of the last operation that has a tail
                lineNumber = self._operationWithTail.GenerateTail(fileHandler, lineNumber, addLineNumbers, digits)
            else: # This is not done yet...
                pass
            return lineNumber
                
        # case 2: given folder + name + ext
        if isinstance(arg, Path) and fileName is not None and fileExtension is not None:
            folder: Path = arg
            folder.mkdir(parents=True, exist_ok=True)
            filename = f"{fileName}{fileExtension}"
            p = folder / filename
            # öppna och skriv via samma inre funktion
            with p.open("w", encoding="utf-8") as fh:
                self._generate_to_file(fh)
            return p

        raise TypeError("Call GenerateTail(fileHandler) or GenerateTail(folderPath, fileName, fileExtension)")
