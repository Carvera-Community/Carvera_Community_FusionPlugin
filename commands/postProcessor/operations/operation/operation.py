from pathlib import Path
from typing import Optional, TextIO

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
from .temporary_post_processing import createTemporaryOperationFile

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
        return self.ctx.subOperationIndexWithTool != -1 and self._operationsDict[self.ctx.subOperationIndexWithTool].hasToolpath

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
        
        program = Programs.Current

        def postProcess(operations, outputFolder, fileName):
            program.SetOutputFolder(outputFolder)
            program.Parameters.Set(Parameters.FILE_NAME, fileName)
            program.Parameters.Set(Parameters.NAME, fileName)
            return program.PostProcess(operations)

        createTemporaryOperationFile(
            self.ctx,
            tmpPath,
            list(self._operationsDict.values()),
            program.fileExtension,
            postProcess,
            parseFile,
        )

    def WriteHeaderStart(self, fileHandle: TextIO) -> None: writeHeaderStart(self.ctx, fileHandle)
    def WriteHeaderEnd(self, fileHandle: TextIO) -> None : writeHeaderEnd(self.ctx, fileHandle)
    def WriteToolComment(self, fileHandle: TextIO) -> None: writeToolComment(self.ctx, fileHandle)
    def WriteHeader(self, fileHandle: TextIO) -> None: writeHeader(self.ctx, fileHandle)
    def WriteBody(self, fileHandle: TextIO) -> None: writeBody(self.ctx, fileHandle)
    def WriteTail(self, fileHandle: TextIO) -> None: writeTail(self.ctx, fileHandle)
