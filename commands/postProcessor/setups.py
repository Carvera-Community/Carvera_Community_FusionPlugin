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
    def Process(cls, tmpPath: Path):
        for setup in cls._items:
            setup.Process(tmpPath)
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
    # Type signatures for tools (mypy/IDE) hints

    # If Generate is called with a fileHandler it means that the output
    # will only be one file
    @overload
    @classmethod
    def GenerateHeader(cls, fileHandler: TextIO, lineNumber: int, addLineNumbers: bool, digits: int) -> int: ...

    # If generate is called with folder + name + ext it means that 
    # multiple files will be generated on lower levels of the hierarchy
    @overload
    @classmethod
    def GenerateHeader(cls, folderPath: Path, lineNumber: int, addLineNumbers: bool, digits: int, fileName: str, fileExtension: str) -> int: ...

    @classproperty
    def headerGenerated(cls) -> bool:
        return cls._headerGenerated

    # Runtime implementation of Generate
    @classmethod
    def GenerateHeader(cls, arg, lineNumber: int, addLineNumbers: bool, digits: int, fileName: Optional[str] = None, fileExtension: Optional[str] = None) -> int:

        briefHeader = False

        # case 1: given an open file (TextIO) means that everything 
        # should be written to it and no directory structure
        # should be created.
        if isinstance(arg, io.TextIOBase) and fileName is None and fileExtension is None:
            fileHandler: TextIO = arg
            for setup in cls.selected:
                lineNumber = setup.GenerateHeader(fileHandler, lineNumber, addLineNumbers, digits, briefHeader)
                if not briefHeader: briefHeader = setup.headerGenerated
            return lineNumber

        # case 2: given folder + name + ext
        if isinstance(arg, Path) and fileName is not None and fileExtension is not None:
            folder: Path = arg
            folder.mkdir(parents=True, exist_ok=True)
            filename = f"{fileName}{fileExtension}"
            p = folder / filename
            # öppna och skriv via samma inre funktion
            with p.open("w", encoding="utf-8") as fh:
                cls._generate_to_file(fh)
            return lineNumber

        raise TypeError("Call GenerateHeader(fileHandler) or GenerateHeader(folderPath, fileName, fileExtension)")
    #endregion

    #region GenerateBody code
    # Type signatures for tools (mypy/IDE) hints

    # If GenerateBody is called with a fileHandler it means that the output
    # will only be one file
    @overload
    @classmethod
    def GenerateBody(cls, fileHandler: TextIO, lineNumber: int, addLineNumbers: bool, digits: int) -> int: ...

    # If GenerateBody is called with folder + name + ext it means that 
    # multiple files will be generated on lower levels of the hierarchy
    @overload
    @classmethod
    def GenerateBody(cls, folderPath: Path, lineNumber: int, addLineNumbers: bool, digits: int, fileName: str, fileExtension: str) -> int: ...

    # Runtime implementation of Generate
    @classmethod
    def GenerateBody(cls, arg, lineNumber: int, addLineNumbers: Optional[bool] = None, digits: Optional[int] = None, fileName: Optional[str] = None, fileExtension: Optional[str] = None) -> int:

        def _writeLine(cls, fileHandler: TextIO, line: str, lineNumber: int, addLineNumbers: bool, digits: int) -> int:
            if addLineNumbers:
                line = f"N{lineNumber:0{digits}} {line}"
            fileHandler.write(f"{line}\n")
            lineNumber += Settings(Settings.NUMBERING_INTERVAL)
            return lineNumber

        # case 1: given an open file (TextIO) means that everything 
        # should be written to it and no directory structure
        # should be created.
        if isinstance(arg, io.TextIOBase) and fileName is None and fileExtension is None:
            fileHandler: TextIO = arg
            firstSetup = None
            for setup in cls.selected:
                if firstSetup is None:
                    firstSetup = setup
                elif Settings(Settings.ROTATE_A_AXIS):
                    # If A-axis rotation is required between setups, insert the rotation code.
                    rotationAngle = -firstSetup.GetRotationAroundXAxisRelativeToDeg(setup)
                    if abs(rotationAngle) > 0.01:
                        lineNumber = _writeLine(cls, fileHandler, "(Rotating between setups)", lineNumber, addLineNumbers, digits)
                        if Settings(Settings.SAFE_Y_RETRACTION):
                            lineNumber = _writeLine(cls, fileHandler, "G90 G53 G0 Z-3 Y{yRetraction}".format(yRetraction=Settings(Settings.Y_RETRACTION_COORDINATE)), lineNumber, addLineNumbers, digits)
                        else:
                            lineNumber = _writeLine(cls, fileHandler, "G90 G53 G0 Z-3", lineNumber, addLineNumbers, digits)
                        lineNumber = _writeLine(cls, fileHandler, "G90 G54 G0 A{:.3f}".format(rotationAngle), lineNumber, addLineNumbers, digits)
                lineNumber = setup.GenerateBody(fileHandler, lineNumber, addLineNumbers, digits, setup != firstSetup)
            return lineNumber
        
        # case 2: given folder + name + ext
        if isinstance(arg, Path) and fileName is not None and fileExtension is not None:
            folder: Path = arg
            folder.mkdir(parents=True, exist_ok=True)
            filename = f"{fileName}{fileExtension}"
            p = folder / filename
            # öppna och skriv via samma inre funktion
            with p.open("w", encoding="utf-8") as fh:
                cls._generate_to_file(fh)
            return lineNumber

        raise TypeError("Call GenerateBody(fileHandler) or GenerateBody(folderPath, fileName, fileExtension)")

    #endregion

    #region GenerateTail code
    # Type signatures for tools (mypy/IDE) hints

    # If GenerateTail is called with a fileHandler it means that the output
    # will only be one file
    @overload
    @classmethod
    def GenerateTail(cls, fileHandler: TextIO, lineNumber: int, addLineNumbers: bool, digits: int): ...

    # If GenerateTail is called with folder + name + ext it means that 
    # multiple files will be generated on lower levels of the hierarchy
    @overload
    @classmethod
    def GenerateTail(cls, folderPath: Path, lineNumber: int, addLineNumbers: bool, digits: int, fileName: str, fileExtension: str): ...

    # Runtime implementation of Generate
    @classmethod
    def GenerateTail(cls, arg, lineNumber: int, addLineNumbers: Optional[bool] = None, digits: Optional[int] = None, fileName: Optional[str] = None, fileExtension: Optional[str] = None):

        # case 1: given an open file (TextIO) means that everything 
        # should be written to it and no directory structure
        # should be created.
        if isinstance(arg, io.TextIOBase) and fileName is None and fileExtension is None:
            fileHandler: TextIO = arg
            setup = next((setup for setup in reversed(cls.selected) if setup.hasOperationWithTail and not setup.isSuppressed), None)
            if setup is not None:
                lineNumber = setup.GenerateTail(fileHandler, lineNumber, addLineNumbers, digits)
            return

        # case 2: given folder + name + ext
        if isinstance(arg, Path) and fileName is not None and fileExtension is not None:
            folder: Path = arg
            folder.mkdir(parents=True, exist_ok=True)
            filename = f"{fileName}{fileExtension}"
            p = folder / filename
            # öppna och skriv via samma inre funktion
            with p.open("w", encoding="utf-8") as fh:
                cls._generate_to_file(fh)
            return

        raise TypeError("Call GenerateTail(fileHandler) or GenerateTail(folderPath, fileName, fileExtension)")
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