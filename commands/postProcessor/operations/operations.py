from pathlib import Path
from typing import List, List, Optional, TextIO

import adsk
from ..line import Line
from ....lib.fusionAddInUtils import Utils
from ..settings.settings import Settings
from .operation.operation import Operation

from .header import OperationsHeader
from .body import OperationsBody
from .tail import OperationsTail

class Operations(Line, OperationsHeader, OperationsBody, OperationsTail):
    def __iter__(self):
        return iter(self._operations)

    def __len__(self):
        return len(self._operations)

    def __getitem__(self, index):
        return self._operations[index]

    def __init__(self, operations: List[adsk.cam.Operation]):
        self._operations = list[Operation]()
        self._operationWithTail: Optional[Operation] = None
        self._operationWithHeader: Optional[Operation] = None
        self._path: Path = None
        self._fileName: str = None
        self._fileExtension: str = None
        self._lineNumber: int = 0

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

            operation = Operation(i)
            operation.Append(operations[i], i, operations[i].hasToolpath) # add first operation
            i += 1
            while i < len(operations):
                if(operations[i].isSuppressed):
                    i += 1
                    continue
                # Append to current group if:
                # - operation has no toolpath, or
                # - current group has no tool yet (we haven't encountered a toolpath), or
                # - we're grouping operations on setup and tool, or
                # - we're combining tools and this op uses the same tool as the current group
                # otherwise finish current group and start a new one
                if (not operations[i].hasToolpath) \
                    or (not operation.hasTool) \
                    or ((Settings.Get(Settings.COMBINE_TOOL) \
                        or Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SETUP_AND_TOOL) \
                        and Operation.GetToolNumber(operations[i]) == operation.toolId):
                    operation.Append(operations[i], i, operations[i].hasToolpath)
                    i += 1
                else:
                    # different tool (or not combining) -> finish current group
                    self._operations.append(operation)
                    break
        if operation is not None: # append final group
            self._operations.append(operation)

    @property
    def lineNumber(self) -> int:
        return self._lineNumber

    def SetLineNumber(self, lineNumber: int) -> None:
        self._lineNumber = lineNumber

    @property
    def tools(self) -> list[adsk.cam.Tool]:
        tools = list[adsk.cam.Tool]()
        for operation in self._operations:
            if operation.hasTool and operation.tool not in tools:
                tools.append(operation.tool)
        return tools

    def Parse(self, tmpPath: Path) -> None:
        for operation in self._operations:
            operation.Parse(tmpPath)
        self._operationWithTail = next((operation for operation in self._operations if operation.hasTail), None)
        self._operationWithHeader = next((operation for operation in self._operations if operation.hasHeader), None)

    def SetOutputPath(self, path: Path) -> None:
        self._path = path

    def SetFileName(self, fileName: str) -> None:
        self._fileName = fileName

    @property
    def fileName(self) -> str:
        return self._fileName

    def SetFileExtension(self, fileExtension: str) -> None:
        self._fileExtension = fileExtension


    def _setOperationFileName(self, operation, toolIdIndex) -> None:
        
        operation.SetFileName(self._fileName)

        if Settings(Settings.OPERATIONS_GROUPING) in [Settings.OperationsGroupings.SINGLE_FILE, 
                                                       Settings.OperationsGroupings.SETUP]:
            return
        
        if Settings(Settings.NUMERIC_NAME):
            # Bump up the file name for the next operation if numeric naming is set
            self._fileName = str(int(self._fileName) + Settings(Settings.FILE_SEQUENCE_INTERVAL)).rjust(Settings(Settings.FILE_SEQUENCE_DIGITS), '0')
        else:
            if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SETUP_AND_TOOL:
                # For setup and tool grouping, use the tool number as 
                # the file name, and append an index if there are 
                # multiple operations with the same tool
                toolIdStr = f"T{operation.toolId}{'_' + str(toolIdIndex) if toolIdIndex > 1 else ''}"
                operation.SetFileName(Utils.sanitizeFilename(toolIdStr, preserveExtension = False))
            elif Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.PER_OPERATION:
                # For per operation grouping, use the operation name as
                # the file name
                operation.SetFileName(Utils.sanitizeFilename(operation.name, preserveExtension = False))

            # If the files should be numbered, prepend the file name 
            # with the operation index to make sure that they will be 
            # sorted correctly
            if Settings(Settings.FILE_SEQUENCE):
                fileNumber = str((operation.index + 1)).rjust(Settings(Settings.FILE_SEQUENCE_DIGITS), '0') 
                operation.SetFileName(f"{fileNumber}_{operation.fileName}")
