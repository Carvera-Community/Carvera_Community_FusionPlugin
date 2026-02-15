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
    def tools(self) -> list[adsk.cam.Tool]:
        tools = list[adsk.cam.Tool]()
        for operation in self._operations:
            if operation.hasTool and operation.tool not in tools:
                tools.append(operation.tool)
        return tools

    def Parse(self, tmpPath: Path):
        for operation in self._operations:
            operation.Parse(tmpPath)
        self._operationWithTail = next((operation for operation in self._operations if operation.hasTail), None)
        self._operationWithHeader = next((operation for operation in self._operations if operation.hasHeader), None)

    def _getFileName(self, fileName: str, operation: Operation, toolNumberIndex: int) -> str:
        outputName = f"_{Utils.sanitizeFilename(operation.name, preserveExtension = False)}"

        # Append operation name and tool number
        if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SETUP_AND_TOOL or Settings(Settings.FLAT_FILE_STRUCTURE):
            outputName = f"{outputName}_T{str(operation.toolId)}"

        # Prepend operation index
        if Settings(Settings.FILE_SEQUENCE):
            outputName = f"{str((operation.index + 1) * Settings(Settings.FILE_SEQUENCE_INTERVAL)).rjust(Settings(Settings.FILE_SEQUENCE_DIGITS), '0')}{outputName}" 

        else:
            # To make sure that files are not overwritten when multiple
            # operations use the same tool, adds an index to the file 
            # name for subsequent occurrences of the same tool
            if toolNumberIndex > 1: 
                outputName = f"{outputName}_{str(toolNumberIndex)}"

        if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SETUP:
            return f"{fileName}"

        if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SETUP_AND_TOOL:
            return outputName

        if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.PER_OPERATION:
            return f"{fileName}_{outputName}"

        return fileName

    def _getFileHandler(self, path: Path, mode: str, fileName: str, operation: Operation, toolNumberIndex: int, fileExtension: str) -> TextIO:
        from ..programs import Programs
        # Numeric file names are always generated in the output folder,
        # no matter what other settings we have and each time we open a
        # file for writing (not appending) we create a new file.
        if Settings(Settings.NUMERIC_NAME) and Programs.Current.fileName.isnumeric():
            filePath = Path(Settings(Settings.OUTPUT_FOLDER)) / f"{Programs.Current.fileName}{fileExtension}"
            return filePath.open(mode, encoding="utf-8")

        filePath = path
        if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SETUP_AND_TOOL:
            filePath = path / Utils.sanitizeFilename(fileName, preserveExtension = False) # Add setup name to the path
        filePath = filePath / f"{self._getFileName(fileName, operation, toolNumberIndex)}{fileExtension}"
        filePath.parent.mkdir(parents=True, exist_ok=True) # Ensure the output folder exists
        return (filePath).open(mode, encoding="utf-8")
