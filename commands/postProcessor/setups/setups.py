from __future__ import annotations
from pathlib import Path
from typing import List, Iterator

import adsk.cam
from ..settings.settings import Settings

from ....lib.fusionAddInUtils.general_utils import Utils, classproperty

from .setup.setup import Setup

from .body import SetupsBody
from .header import SetupsHeader
from .tail import SetupsTail

class _SetupsMeta(type):
    def __iter__(cls) -> Iterator[Setup]:
        """Iterate over stored setups.

        Typing hint ensures `for s in Setups:` is treated as `Setup` by
        type checkers (mypy/pyright).
        """
        return iter(cls._items)
    
class Setups(SetupsHeader, SetupsBody, SetupsTail, metaclass=_SetupsMeta):
    
    _items: List[Setup] = []
    _headerGenerated: bool = False
    _fileExtension: str = '.'
    _path: Path = None
    _fileName: str = None
    _lineNumber: int = 0

    @classmethod
    def SetLineNumber(cls, lineNumber: int) -> None:
        cls._lineNumber = lineNumber

    @classmethod
    def Load(cls, setups: adsk.cam.Setups) -> None:
        noneSelected = not any((setup.isSelected and not setup.isSuppressed and not setup.hasError for setup in setups))
        cls._items: List[Setup] = [Setup(setup, index, noneSelected) for index, setup in enumerate(setups)]

    @classmethod
    def Parse(cls, tmpPath: Path) -> None:
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
                signed_angle = round(first.GetRotationAroundXAxisRelativeToDeg(setup), 3)
                if signed_angle != 0:
                    needsRotation.append((setup.name, signed_angle))
                    Utils.log(f"Setups: WCS needs rotation: {signed_angle} degrees difference.")
        return (len(needsRotation) != 0, needsRotation)

    @classmethod
    def RenameAll(cls, find, replace, isRegex) -> None:
        for setup in cls._items:
            setup.Rename(find, replace, isRegex)

    @classproperty
    def selected(cls) -> List[Setup]:
        return [setup for setup in cls._items if setup.isSelected and not setup.isSuppressed and not setup.hasError]
    
    @classproperty
    def hasSelected(cls) -> bool:
        return any(setup.isSelected and not setup.isSuppressed for setup in cls._items)

    @classproperty
    def hasOperationWithTail(cls) -> bool:
        return any(setup.hasOperationWithTail and not setup.isSuppressed for setup in cls._items)

    @classproperty
    def Count(cls) -> int:
        return len(cls.selected)
    
    @classmethod
    def SetFileExtension(cls, extension: str) -> None:
        for setup in cls.selected:
            setup.SetFileExtension(extension)

    @classmethod
    def SetPath(cls, path: Path) -> None:
        outputPath: Path = path
        for setup in cls.selected:
            if not (Settings(Settings.FLAT_FILE_STRUCTURE) \
                    or Settings(Settings.NUMERIC_NAME) \
                    or Settings(Settings.OPERATIONS_GROUPING) in [Settings.OperationsGroupings.SINGLE_FILE, 
                                                                  Settings.OperationsGroupings.SETUP]):
                fileNumber = str(setup.index + 1).rjust(Settings(Settings.FILE_SEQUENCE_DIGITS), "0") + '_' if Settings(Settings.FILE_SEQUENCE) else ""
                outputPath = path / f"{fileNumber}{Utils.sanitizeFilename(setup.name, preserveExtension = False)}"
            setup.SetOutputPath(outputPath)

    @classmethod
    def SetFileName(cls, fileName: str) -> None:
        for setup in cls.selected:
            if Settings(Settings.FLAT_FILE_STRUCTURE):
                fileName = f"{fileName}_{Utils.sanitizeFilename(setup.name, preserveExtension = False)}"
            elif Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SINGLE_FILE \
                or Settings(Settings.NUMERIC_NAME):
                setup.SetFileName(fileName)
                
    @classproperty
    def tools(cls) -> list[adsk.cam.Tool]:
        tools = list[adsk.cam.Tool]()
        for setup in cls.selected:
            tools.extend(setup.tools)
        return tools