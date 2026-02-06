from __future__ import annotations
import io
import io
import math
import os
from pathlib import Path
from typing import List, Optional, TextIO, overload, Iterator

import adsk.cam
from .settings import Settings
from ...lib.fusionAddInUtils.general_utils import Utils, classproperty

from .setup import Setup

class _SetupsMeta(type):
    def __iter__(cls) -> Iterator[Setup]:
        """Iterate over stored setups.

        Typing hint ensures `for s in Setups:` is treated as `Setup` by
        type checkers (mypy/pyright).
        """
        return iter(cls._items)
    
class Setups(metaclass=_SetupsMeta):
    
    _outputFileName: str = None
    _items: List[Setup] = []
    _headerGenerated: bool = False

    @classmethod
    def SetOutputFileName(cls, fileName):
        cls._outputFileName = fileName

    @classmethod
    def Load(cls, setups: adsk.cam.Setups):
        noneSelected = not any((setup.isSelected and not setup.isSuppressed for setup in setups))
        cls._items: List[Setup] = [Setup(setup, noneSelected) for setup in setups if not setup.isSuppressed]

    @classmethod
    def Parse(cls, tmpPath: Path):
        for setup in cls.selected:
            setup.Parse(tmpPath)
        return
    
    @classmethod
    def getWCSAlignmentIssues(cls) -> tuple[bool, list[str], list[str]]:
        misalignedOrigin = []
        misalignedXAxis = []
        first = None
        for setup in cls.selected:
            if first is None:
                first = setup
            else:
                if not first.origin.isEqualTo(setup.origin):
                    misalignedOrigin.append(setup.name)
                if not first.xNormal.isParallelTo(setup.xNormal):
                    misalignedXAxis.append(setup.name)
        return (len(misalignedOrigin) + len(misalignedXAxis) == 0, misalignedOrigin, misalignedXAxis)

    @classmethod
    def AAxisRotationRequired(cls) -> tuple[bool, list[tuple[str, float]]]:
        needsRotation = []
        first = None
        for setup in cls.selected:
            if first is None:
                first = setup
            else:
                signed_angle = math.round(first.GetRotationAroundXAxisRelativeToDeg(setup)*10)/10.0
                if signed_angle != 0:
                    needsRotation.append((setup.name, signed_angle))
                    Utils.log(f"Setups: WCS needs rotation: {signed_angle} degrees difference.")
        return (len(needsRotation) != 0, needsRotation)

    #region GenerateHeader code
    # Type signatures for tools hints
    @overload
    @classmethod
    def GenerateHeader(cls, fileHandler: TextIO, lineNumber: int, addLineNumbers: bool, digits: int) -> int: ...

    @overload
    @classmethod
    def GenerateHeader(cls, folderPath: Path, lineNumber: int, addLineNumbers: bool, digits: int, fileName: str, fileExtension: str) -> int: ...

    @classmethod
    def GenerateHeader(cls, pathOrFile, lineNumber: int, addLineNumbers: bool, digits: int, fileName: Optional[str] = None, fileExtension: Optional[str] = None) -> int:

        fileHandlerParam: Optional[TextIO] = None

        if isinstance(pathOrFile, io.TextIOBase):
            fileHandlerParam: TextIO = pathOrFile
            fileHandler: TextIO = fileHandlerParam

        try:
            firstSetup = next((setup for setup in cls.selected), None)

            if firstSetup is None: # No setups, exit early
                return lineNumber
            
            # For a single file output, there is only one header.
            if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SINGLE_FILE:
                if fileHandlerParam is None: fileHandler = cls._getFileHandler(cls.FileModes.WRITE, pathOrFile, fileName, firstSetup.name, fileExtension)
                lineNumber = firstSetup.WriteSetupName(fileHandler, addLineNumbers, lineNumber, digits)
                lineNumber = firstSetup.WriteHeaderStart(fileHandler, addLineNumbers, lineNumber, digits)

            for setup in cls.selected:
                # One header per setup
                if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SETUP:
                    if fileHandlerParam is None: fileHandler = cls._getFileHandler(cls.FileModes.WRITE, pathOrFile, fileName, setup.name, fileExtension)
                    lineNumber = setup.WriteHeaderStart(fileHandler, addLineNumbers, lineNumber, digits)

                # Put the tool comments in the header file we're working on at the moment
                if fileHandlerParam is None: fileHandler = cls._getFileHandler(cls.FileModes.APPEND, pathOrFile, fileName, setup.name, fileExtension)
                lineNumber = setup.WriteToolComment(fileHandler, addLineNumbers, lineNumber, digits)

                # If grouping by setup, also write the header end in the same file after the tool comments
                if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SETUP:
                    if fileHandlerParam is None: fileHandler = cls._getFileHandler(cls.FileModes.APPEND, pathOrFile, fileName, setup.name, fileExtension)
                    lineNumber = setup.WriteHeaderEnd(fileHandler, addLineNumbers, lineNumber, digits)

            # If writing to a single file, write the header end after all tool comments have been written for all setups
            if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SINGLE_FILE:
                if fileHandlerParam is None: fileHandler = cls._getFileHandler(cls.FileModes.APPEND, pathOrFile, fileName, firstSetup.name, fileExtension)
                lineNumber = firstSetup.WriteHeaderEnd(fileHandler, addLineNumbers, lineNumber, digits)

            return lineNumber

        finally:
            if fileHandlerParam is None and fileHandler is not None: # local filehandler was opened, so close it
                fileHandler.close()

    class FileModes:
        READ = 'r'
        WRITE = 'w'
        APPEND = 'a'

    @classmethod
    def _getFileHandler(cls, mode: FileModes, path: Path, fileName: str, setupName: str, fileExtension: str) -> TextIO:
        fileName = f"{fileName}_{setupName}" if Settings(Settings.FLAT_FILE_STRUCTURE) else setupName
        setupFile = path / f"{fileName}{fileExtension}"
        return setupFile.open(mode, encoding="utf-8")

    #endregion

    #region GenerateBody code
    @overload
    @classmethod
    def GenerateBody(cls, fileHandler: TextIO, lineNumber: int, addLineNumbers: bool, digits: int) -> int: ...

    @overload
    @classmethod
    def GenerateBody(cls, folderPath: Path, lineNumber: int, addLineNumbers: bool, digits: int, fileName: str, fileExtension: str) -> int: ...

    @classmethod
    def GenerateBody(cls, pathOrFile, lineNumber: int, addLineNumbers: Optional[bool] = None, digits: Optional[int] = None, fileName: Optional[str] = None, fileExtension: Optional[str] = None) -> int:

        fileHandlerParam: Optional[TextIO] = None
        firstSetup: Optional[bool] = None
        rotationAngle: float = 0
        currentRotationAngle: float = None
        preserveRotation: bool = False

        if isinstance(pathOrFile, io.TextIOBase) and fileName is None and fileExtension is None:
            fileHandlerParam: TextIO = pathOrFile
            fileHandler: TextIO = fileHandlerParam
        try:
            for setup in cls.selected:
                if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SINGLE_FILE:
                    if fileHandlerParam is None: fileHandler = cls._getFileHandler(cls.FileModes.APPEND, pathOrFile, fileName, setup.name, fileExtension)
                    lineNumber = setup.WriteSetupName(fileHandler, addLineNumbers, lineNumber, digits)

                if Settings(Settings.ROTATE_A_AXIS):
                    angle = 0 if firstSetup is None else setup.GetRotationAroundXAxisRelativeToDeg(firstSetup)
                    rotationAngle = None if angle == currentRotationAngle else angle
                    currentRotationAngle = angle
                    preserveRotation = firstSetup is None
                else:
                    preserveRotation = True # We don't want to do any changes to the native rotation code

                if fileHandlerParam is None: fileHandler = cls._getFileHandler(cls.FileModes.APPEND, pathOrFile, fileName, setup.name, fileExtension)
                lineNumber = setup.GenerateBody(fileHandler, lineNumber, addLineNumbers, digits, setup != firstSetup, rotationAngle = rotationAngle, preserveRotation = preserveRotation)

                if firstSetup is None:
                    firstSetup = setup
            return lineNumber
        
        finally:
            if fileHandlerParam is None and fileHandler is not None: # local filehandler was opened, so close it
                fileHandler.close()

    #endregion

    #region GenerateTail code
    @overload
    @classmethod
    def GenerateTail(cls, fileHandler: TextIO, lineNumber: int, addLineNumbers: bool, digits: int): ...

    @overload
    @classmethod
    def GenerateTail(cls, folderPath: Path, lineNumber: int, addLineNumbers: bool, digits: int, fileName: str, fileExtension: str): ...

    # Runtime implementation of Generate
    @classmethod
    def GenerateTail(cls, pathOrFile, lineNumber: int, addLineNumbers: Optional[bool] = None, digits: Optional[int] = None, fileName: Optional[str] = None, fileExtension: Optional[str] = None):

        fileHandlerParam: Optional[TextIO] = None

        if isinstance(pathOrFile, io.TextIOBase):
            fileHandlerParam: TextIO = pathOrFile
            fileHandler: TextIO = fileHandlerParam
        
        try:
            # One tail for the whole program.
            if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SINGLE_FILE:
                setup = next((setup for setup in cls.selected if setup.hasTail and not setup.isSuppressed), None)
                if setup is None:
                    return lineNumber

                if fileHandlerParam is None: fileHandler = cls._getFileHandler(cls.FileModes.APPEND, pathOrFile, fileName, setup.name, fileExtension)
                lineNumber = setup.GenerateTail(fileHandler, lineNumber, addLineNumbers, digits)

            # One tail per setup
            if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SETUP:
                for setup in cls.selected:
                    if fileHandlerParam is None: fileHandler = cls._getFileHandler(cls.FileModes.APPEND, pathOrFile, fileName, setup.name, fileExtension)
                    lineNumber = setup.GenerateTail(fileHandler, lineNumber, addLineNumbers, digits)


            return lineNumber
        finally:
            if fileHandlerParam is None and fileHandler is not None: # local filehandler was opened, so close it
                fileHandler.close()
    #endregion

    @classmethod
    def RenameAll(cls, find, replace, isRegex):
        for setup in cls._items:
            setup.Rename(find, replace, isRegex)

    @classproperty
    def selected(cls) -> List[Setup]:
        return [setup for setup in cls._items if setup.isSelected and not setup.isSuppressed]
    
    @classproperty
    def hasSelected(cls) -> bool:
        return any(setup.isSelected and not setup.isSuppressed for setup in cls._items)

    @classproperty
    def hasOperationWithTail(cls) -> bool:
        return any(setup.hasOperationWithTail and not setup.isSuppressed for setup in cls._items)

    @classproperty
    def Count(cls) -> int:
        return len(cls.selected)