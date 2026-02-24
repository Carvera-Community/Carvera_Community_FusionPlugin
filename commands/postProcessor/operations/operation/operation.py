from pathlib import Path
from typing import Optional
import uuid

import adsk.cam

from .....lib.fusionAddInUtils.general_utils import Utils

from ...parameters import Parameters
from ...strings import Strings

from .parser import OperationParser
from .header import OperationHeader
from .body import OperationBody
from .tail import OperationTail

class Operation(OperationParser, OperationHeader, OperationBody, OperationTail):    
    def __init__(self, index: int):
        self._outputFilePath: Path = None
        # As there can be multiple operations without tools they are 
        # grouped with the previous operation (or next if it is the 
        # first operation missing a tool)
        self._operationsDict: dict[int, adsk.cam.Operation] = {}  
        
        self._index = index
        self._operationWithTool: int = -1
        self._tempFilePath: Path = None
        self._allowBlankLines: bool = False

        self._fileName: str = None
        self._lineNumber: int = 0

        self._headerEndLine: int = -1
        self._bodyStartLine: int = -1
        self._rotationLine: int = -1
        self._tailStartLine: int = -1
        self._rapidsAnalysis: dict[int, int] = {} # line number of rapid move start -> line number of rapid move end

    def Append(self, operation: adsk.cam.Operation, index, hasTool: bool):
        self._operationsDict[index] = operation
        if hasTool:
            self._operationWithTool = index

    @property
    def fileName(self) -> str:
        return self._fileName
    
    def SetFileName(self, fileName: str):
        self._fileName = fileName

    @property
    def index(self) -> int:
        return self._index

    @property
    def lineNumber(self) -> int:
        return self._lineNumber

    def SetLineNumber(self, lineNumber: int):
        self._lineNumber = lineNumber

    @property
    def toolId(self) -> Optional[int]:
        return Operation.GetToolNumber(self._operationsDict[self._operationWithTool]) if self.hasTool else None

    @property
    def hasTool(self) -> bool:
        return self._operationWithTool is not -1 and self._operationsDict[self._operationWithTool].hasToolpath

    @property
    def name(self) -> str:
        names = "-".join(operation.name for operation in self._operationsDict.values())
        if len(names) > Utils.maxFilenameLength() - 10:
            return Strings("Combined Operations ({operationsCount})".format(operationsCount=len(self._operationsDict)))
        return names

    @property
    def tool(self) -> Optional[adsk.cam.Tool]:
        if self._operationWithTool == -1:
            return None
        return self._operationsDict[self._operationWithTool].tool

    @property
    def firstIndex(self) -> int:
        return min(self._operationsDict.keys())

    @property
    def tempFilePath(self) -> Path:
        return self._tempFilePath
    
    @property
    def hasHeader(self) -> bool:
        return self._headerEndLine != -1

    @property
    def hasBody(self) -> bool:
        return self._bodyStartLine != -1
    
    @property
    def hasTail(self) -> bool:
        return self._tailStartLine != -1
    
    @property
    def hasRotation(self) -> bool:
        return self._rotationLine != -1

    def SetOutputPath(self, path: Path):
        self._outputFilePath = path

    @staticmethod
    def GetToolDescription(operation):
        return operation.tool.description if operation.hasToolpath else Strings("<No tool>")

    @staticmethod
    def GetToolNumber(operation):
        return operation.tool.parameters.itemByName("tool_number").value.value

    def Parse(self, tmpPath: Path):
        from ...programs import Programs

        name = uuid.uuid4().hex + Programs.Current.fileExtension
        self._tempFilePath = tmpPath / name

        Programs.Current.SetOutputFolder(self._tempFilePath.parent)
        Programs.Current.Parameters.Set(Parameters.FILE_NAME, self._tempFilePath.stem)
        Programs.Current.Parameters.Set(Parameters.NAME, self._tempFilePath.stem)
        if not Programs.Current.PostProcess(list(self._operationsDict.values())):
            raise Exception(f"Operation {self.name} post processing failed.")
        
        time = 0.1
        loops = 0
        # Wait maximally 5.5 seconds for the file to be created, as 
        # sometimes it is not immediately available after post 
        # processing
        while not self._tempFilePath.exists() and loops < 10: 
            loops += 1
            time.sleep(time * loops)
        if loops >= 10 or not self._tempFilePath.exists():
            raise Exception(f"Operation {self.name} post processing failed: output file was not created.")

        self._parseFile(self._tempFilePath)
