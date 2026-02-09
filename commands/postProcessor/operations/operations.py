import io
from pathlib import Path
from typing import List, List, Optional, TextIO, overload

import adsk
from ..line import Line
from ....lib.fusionAddInUtils import Utils
from ..settings.settings import Settings
from .operation.operation import Operation


class Operations(Line):
    def __init__(self, operations: List[adsk.cam.Operation]):
        self._operations = list[Operation]()
        self._operationWithTail: Operation = None

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
            operation.Append(operations[i], i, operations[i].hasToolpath) # add first operation
            i += 1
            while i < len(operations):
                if(operations[i].isSuppressed):
                    i += 1
                    continue
                # Append to current group if:
                # - operation has no toolpath, or
                # - current group has no tool yet (we haven't encountered a toolpath), or
                # - we're combining tools and this op uses the same tool as the current group
                # otherwise finish current group and start a new one
                if (not operations[i].hasToolpath) \
                    or (not operation.hasTool) \
                    or (Settings.Get(Settings.COMBINE_TOOL) \
                        and Operation.GetToolNumber(operations[i]) == operation.toolId):
                    operation.Append(operations[i], i, operations[i].hasToolpath)
                    i += 1
                else:
                    # different tool (or not combining) -> finish current group
                    self._operations.append(operation)
                    break
        if operation is not None: # append final group
            self._operations.append(operation)
                
    def SetOutputFolder(self, folder):
        self._outputFolder = folder

    def Parse(self, tmpPath: Path):
        for operation in self._operations:
            operation.Parse(tmpPath)
        self._operationWithTail = next((op for op in self._operations if op.hasTail), None)

    def WriteHeaderStart(self, fileHandler: TextIO, lineNumber: int) -> int:
        firstOperation =  next((operation for operation in self._operations if operation.hasTool), None)
        if firstOperation is not None:
            if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.PER_OPERATION:
                pass # TODO
            else:
                lineNumber = firstOperation.WriteHeaderStart(fileHandler, lineNumber)
        return lineNumber

    def WriteToolComment(self, fileHandler: TextIO, lineNumber: int) -> int:
        for operation in self._operations:
            if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.PER_OPERATION:
                pass # TODO
            else:
                lineNumber = operation.WriteToolComment(fileHandler, lineNumber)
        return lineNumber

    def WriteHeaderEnd(self, fileHandler: TextIO, lineNumber: int) -> int:
        if self._operationWithTail is not None:
            if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.PER_OPERATION:
                pass # TODO
            else:
                lineNumber = self._operationWithTail.WriteHeaderEnd(fileHandler, lineNumber)
        return lineNumber

    @overload
    def WriteBody(self, fileHandler: TextIO, lineNumber: int, *, rotationAngle: Optional[float] = None, preserveRotation: Optional[bool] = False) -> int: ...

    # If GenerateBody is called with folder it means that 
    # multiple files will be generated on lower levels of the hierarchy
    @overload
    def WriteBody(self, folderPath: Path, lineNumber: int, fileName: str, fileExtension: str, *, rotationAngle: Optional[float] = None, preserveRotation: Optional[bool] = False) -> int: ...

    # Runtime implementation of GenerateBody
    def WriteBody(self, pathOrFile, lineNumber: int, fileName: Optional[str] = None, fileExtension: Optional[str] = None, *, rotationAngle: Optional[float] = None, preserveRotation: Optional[bool] = False) -> int:

        # case 1: given an open file (TextIO) means that everything 
        # should be written to it and no directory structure
        # should be created.

        if isinstance(pathOrFile, io.TextIOBase) and fileName is None and fileExtension is None:
            fileHandler: TextIO = pathOrFile
            i = 0
            for operation in self._operations:
                if operation.hasBody:
                    lineNumber = operation.WriteBody(fileHandler, lineNumber, rotationAngle = rotationAngle, preserveRotation = preserveRotation)
                    rotationAngle = None # Only apply rotation to the first operation if specified, then reset to None so that subsequent operations are not rotated
                    preserveRotation = False # Only preserve rotation for the first operation if specified, then reset to False so that subsequent operations do not preserve rotation
                i += 1
            return lineNumber
                
        # case 2: given folder + name + ext means that we should create files for each operation in the given folder
        if isinstance(pathOrFile, Path) and fileName is not None and fileExtension is not None:
            folder: Path = pathOrFile
            # Lets not make a folder per operation...
            # if not Settings(Settings.FLAT_FILE_STRUCTURE):
            #     folder = arg / operation.name
            folder.mkdir(parents=True, exist_ok=True)
            for operation in self._operations:
                if Settings(Settings.FLAT_FILE_STRUCTURE):
                    filename = f"{fileName}_{operation.name}{fileExtension}"
                else: # We should be in a folder named after the setup, create the operation file directly.
                    filename = f"{fileName}{fileExtension}"
                operationFile = folder / filename
                with operationFile.open("w", encoding="utf-8") as fileHandler:
                    lineNumber = operation.WriteBody(fileHandler, lineNumber, rotationAngle = rotationAngle, preserveRotation = preserveRotation)
                    rotationAngle = None # Only apply rotation to the first operation if specified, then reset to None so that subsequent operations are not rotated
            

        raise TypeError("Call GenerateBody(fileHandler) or GenerateBody(folderPath, fileName, fileExtension)")

    @property
    def hasTail(self):
        return self._operationWithTail is not None

    # Type signatures for tools (mypy/IDE) hints

    # If GenerateTail is called with a fileHandler it means that the output
    # will only be one file
    @overload
    def WriteTail(self, fileHandler: TextIO, lineNumber: int) -> int: ...

    # If GenerateTail is called with folder it means that 
    # multiple files will be generated on lower levels of the hierarchy
    @overload
    def WriteTail(self, folderPath: Path, lineNumber: int, fileName: str, fileExtension: str) -> int: ...

    # Runtime implementation of GenerateTail
    def WriteTail(self, arg, lineNumber: int, fileName: Optional[str] = None, fileExtension: Optional[str] = None) -> int:

        if self._operationWithTail is None:
            return lineNumber

        # case 1: given an open file (TextIO) means that everything 
        # should be written to it and no directory structure
        # should be created.
        toolComments = []

        if isinstance(arg, io.TextIOBase) and fileName is None and fileExtension is None:
            fileHandler: TextIO = arg
                
            # Attach the tail of the last operation that has a tail
            lineNumber = self._operationWithTail.WriteTail(fileHandler, lineNumber)
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

    def WriteOperations(self, folderPath: Path, fileName: str, fileExtension: str, *, rotationAngle: Optional[float] = None, preserveRotation: Optional[bool] = False) -> int:
        for operation in self._operations:
            operationFileName = Utils.sanitizeFilename(operation.name, preserveExtension = False)
            outputName = "{index}_{fileName}".format(
                fileName = operationFileName, 
                index=str(operation.firstIndex + 1).rjust(2, '0')) if Settings(Settings.SEQUENCE) in (Settings.Sequences.FILE, Settings.Sequences.FILE_AND_STEP) else fileName
            outputName = ("{fileName}_{operationName}{fileExtension}" if Settings(Settings.FLAT_FILE_STRUCTURE) else "{operationName}{fileExtension}") \
                .format(
                    fileName = fileName, 
                    operationName = outputName, 
                    fileExtension = fileExtension)
            operationFile = folderPath / outputName
            with operationFile.open("w", encoding="utf-8") as fileHandler:
                lineNumber = 0 # Writing operations separately, so line numbers start at 0 for each file
                lineNumber = Operations._writeLine(fileHandler, f"({operationFile.stem})", lineNumber)
                lineNumber = operation.WriteHeaderStart(fileHandler, lineNumber)
                lineNumber = operation.WriteToolComment(fileHandler, lineNumber)
                lineNumber = operation.WriteHeaderEnd(fileHandler, lineNumber)
                lineNumber = operation.WriteBody(fileHandler, lineNumber, rotationAngle = rotationAngle, preserveRotation = preserveRotation)
                lineNumber = operation.WriteTail(fileHandler, lineNumber)
        return lineNumber