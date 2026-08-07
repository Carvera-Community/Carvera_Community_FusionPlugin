from pathlib import Path
import time
from typing import Optional, TextIO
import uuid

from adsk import cam
from .....lib.fusionParameters.cast_cam_param import castCAMParam
from .....lib.fusionAddInUtils.general_utils import Utils
from ...parameters import Parameters
from ...strings import Strings
from .parser import parseFile
from .operation_context import OperationContext
from .header_writer import (
    writeHeaderStart,
    writeHeaderEnd,
    writeToolComment,
    writeHeader
)
from .body_writer import writeBody
from .tail_writer import writeTail

class Operation():    
    def __init__(self, ctx: OperationContext):
        self._outputFilePath: Path | None = None
        self.ctx = ctx
        # As there can be multiple operations without tools they are 
        # grouped with the previous operation (or next if it is the 
        # first operation missing a tool)
        self._operationsDict: dict[int, cam.Operation] = {}  
        

    def Append(self, operation: cam.Operation, index, hasTool: bool):
        self._operationsDict[index] = operation
        if hasTool:
            self.ctx.subOperationIndexWithTool = index

        names = "-".join(operation.name for operation in self._operationsDict.values())
        if len(names) > Utils.maxFilenameLength() - 10:
            self.ctx.name = Strings("Combined Operations ({operationsCount})".format(operationsCount=len(self._operationsDict)))
        else:
            self.ctx.name = names


    @property
    def name(self) -> str:
        return self.ctx.name
    
    @property
    def fileName(self) -> str | None:
        return self._fileName
    
    def SetFileName(self, fileName: str):
        self._fileName = fileName

    @property
    def index(self) -> int:
        return self.ctx.index

    @property
    def lineNumber(self) -> int:
        return self._lineNumber

    def SetLineNumber(self, lineNumber: int):
        self._lineNumber = lineNumber

    @property
    def toolId(self) -> Optional[int]:
        return Operation.GetToolNumber(self._operationsDict[self.ctx.subOperationIndexWithTool]) if self.hasTool else None

    @property
    def hasTool(self) -> bool:
        return self.ctx.subOperationIndexWithTool is not -1 and self._operationsDict[self.ctx.subOperationIndexWithTool].hasToolpath

    @property
    def tool(self) -> Optional[cam.Tool]:
        if self.ctx.subOperationIndexWithTool == -1:
            return None
        return self._operationsDict[self.ctx.subOperationIndexWithTool].tool

    @property
    def firstIndex(self) -> int:
        return min(self._operationsDict.keys())

    @property
    def tempFilePath(self) -> Path:
        return self.ctx.tempFilePath
    
    @property
    def hasHeader(self) -> bool:
        return self.ctx.headerEndLine != -1

    @property
    def hasBody(self) -> bool:
        return self.ctx.bodyStartLine != -1
    
    @property
    def hasTail(self) -> bool:
        return self.ctx.tailStartLine != -1
    
    @property
    def hasRotation(self) -> bool:
        return self.ctx.hasRotation

    def SetOutputPath(self, path: Path):
        self._outputFilePath = path

    @staticmethod
    def GetToolDescription(operation) -> str:
        return operation.tool.description if operation.hasToolpath else Strings("<No tool>")

    @staticmethod
    def GetToolNumber(operation) -> int:
        return castCAMParam.ToInt(operation.tool.parameters.itemByName("tool_number"))

    def Parse(self, tmpPath: Path):
        from ...programs import Programs

        if Programs.Current is None:
            raise ValueError("Programs.Current is None")
        
        name = uuid.uuid4().hex + ('' if Programs.Current.fileExtension is None else Programs.Current.fileExtension)
        self.ctx.tempFilePath = tmpPath / name

        Programs.Current.SetOutputFolder(self.ctx.tempFilePath.parent)
        Programs.Current.Parameters.Set(Parameters.FILE_NAME, self.ctx.tempFilePath.stem)
        Programs.Current.Parameters.Set(Parameters.NAME, self.ctx.tempFilePath.stem)
        if not Programs.Current.PostProcess(list(self._operationsDict.values())):
            raise Exception(f"Operation {self.ctx.name} post processing failed.")
        
        sleepTime = 0.1
        loops = 0
        # Wait maximally 5.5 seconds for the file to be created, as 
        # sometimes it is not immediately available after post 
        # processing
        while not self.ctx.tempFilePath.exists() and loops < 10: 
            loops += 1
            time.sleep(sleepTime * loops)
        if loops >= 10 or not self.ctx.tempFilePath.exists():
            raise Exception(f"Operation {self.ctx.name} post processing failed: output file was not created.")

        parseFile(self.ctx)

    def WriteHeaderStart(self, fileHandle: TextIO) -> None: writeHeaderStart(self.ctx, fileHandle)
    def WriteHeaderEnd(self, fileHandle: TextIO) -> None : writeHeaderEnd(self.ctx, fileHandle)
    def WriteToolComment(self, fileHandle: TextIO) -> None: writeToolComment(self.ctx, fileHandle)
    def WriteHeader(self, fileHandle: TextIO) -> None: writeHeader(self.ctx, fileHandle)
    def WriteBody(self, fileHandle: TextIO) -> None: writeBody(self.ctx, fileHandle)
    def WriteTail(self, fileHandle: TextIO) -> None: writeTail(self.ctx, fileHandle)