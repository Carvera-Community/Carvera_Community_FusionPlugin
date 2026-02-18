from ..settings.settings import Settings
from ..file_modes import FileModes

from .operation.operation import Operation

class OperationsBody:

    def WriteBody(self, rotationAngle: float, preserveRotation: bool):

        toolIdIndex = {}
        #firstOperationPerTool = dict[int, Operation]()
        operation: Operation
        for operation in [op for op in self._operations if op.hasBody]:
            toolId = operation.toolId
            if toolId not in toolIdIndex:
                toolIdIndex[toolId] = 0
            toolIdIndex[toolId] += 1

            self._setOperationFileName(operation, toolIdIndex[toolId])

            with (self._path / f"{operation.fileName}{self._fileExtension}").open(FileModes.APPEND) as fileHandler:
                if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.PER_OPERATION:
                    # Line number is saved in the operation when writing the header, no need to set it here
                    pass
                #elif Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SETUP_AND_TOOL:
                    # Line number is stored in the first operation of 
                    # each tool when writing the header, so it can be used here
                    #if firstOperationPerTool.get(toolId) is None:
                    #    firstOperationPerTool[toolId] = operation
                    #else:
                    #    operation.SetLineNumber(firstOperationPerTool[toolId].lineNumber)
                elif Settings(Settings.OPERATIONS_GROUPING) in [Settings.OperationsGroupings.SINGLE_FILE, 
                                                                Settings.OperationsGroupings.SETUP]:
                    # Line number is saved in the setup (operations) when writing the header, so it can be used here
                    operation.SetLineNumber(self._lineNumber)
                
                operation.WriteBody(fileHandler, rotationAngle, preserveRotation)
                #if firstOperationPerTool.get(toolId) is not None:
                #    firstOperationPerTool[toolId].SetLineNumber(operation.lineNumber)
                self._lineNumber = operation.lineNumber

                rotationAngle = None # Only apply rotation to the first operation if specified as the rotation is applied on a setup level
                preserveRotation = False # Only preserve rotation for the first operation if specified as the rotation is applied on a setup level
