import io
from pathlib import Path
import re
import tempfile
import time
from typing import TYPE_CHECKING, Final, Optional, TextIO, overload
import uuid
import uuid

import adsk

if TYPE_CHECKING:
    from .operations import Operations

from .operation_parser import OperationParser
from .operation_header import OperationHeader
from .operation_body import OperationBody
from .operation_tail import OperationTail
from .parameters import Parameters

class Operation(OperationParser, OperationHeader, OperationBody, OperationTail):    
    def __init__(self):
        self._outputFileName = None
        # As there can be multiple operations without tools they are 
        # grouped with the previous operation (or next if it is the 
        # first operation missing a tool)
        self._operationsList = list[adsk.cam.Operation]()    
        
        self._operationWithTool = None
        self._tempFilePath: Path = None
        self._allowBlankLines = False
        self._headerGenerated = False

        self._headerEndLine = -1
        self._bodyStartLine = -1
        self._rotationLine = -1
        self._tailStartLine = -1

    def Append(self, operation: adsk.cam.Operation, hasTool: bool):
        self._operationsList.append(operation)
        if hasTool:
            self._operationWithTool = operation

    @property
    def toolId(self):
        return Operations.GetToolNumber(self._operationWithTool) if self.hasTool else None

    @property
    def hasTool(self):
        return self._operationWithTool is not None and self._operationWithTool.hasToolpath

    @property
    def name(self):
        return self._operationWithTool.name if self._operationWithTool is not None else "NoToolOperation"

    @property
    def tempFilePath(self) -> Path:
        return self._tempFilePath
    
    @property
    def hasBody(self) -> bool:
        return self._bodyStartLine != -1
    
    @property
    def hasTail(self) -> bool:
        return self._tailStartLine != -1
    
    @property
    def hasRotation(self) -> bool:
        return self._rotationLine != -1

    @property
    def headerGenerated(self) -> bool:
        return self._headerGenerated

    def Parse(self, tmpPath: Path):
        from .programs import Programs

        name = uuid.uuid4().hex + Programs.Current.fileExtension
        self._tempFilePath = tmpPath / name

        Programs.Current.SetOutputFolder(self._tempFilePath.parent)
        Programs.Current.Parameters.Set(Parameters.FILE_NAME, self._tempFilePath.stem)
        Programs.Current.Parameters.Set(Parameters.NAME, self._tempFilePath.stem)
        if not Programs.Current.PostProcess(self._operationsList):
            raise Exception(f"Operation {self.name} post processing failed.")
        time.sleep(0.1) # files missing sometimes unless we slow down (??)

        self._parseFile(self._tempFilePath)