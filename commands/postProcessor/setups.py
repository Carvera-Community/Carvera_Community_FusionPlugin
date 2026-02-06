from __future__ import annotations
import math
from pathlib import Path
from typing import List, TextIO, Iterator

import adsk.cam

from ...lib.fusionAddInUtils.general_utils import Utils, classproperty

from .settings import Settings
from .setup import Setup

from .setups_body import SetupsBody
from .setups_header import SetupsHeader
from .setups_tail import SetupsTail

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

    class FileModes:
        READ = 'r'
        WRITE = 'w'
        APPEND = 'a'

    @classmethod
    def _getFileHandler(cls, mode: FileModes, path: Path, fileName: str, setupName: str, fileExtension: str) -> TextIO:
        fileName = f"{fileName}_{setupName}" if Settings(Settings.FLAT_FILE_STRUCTURE) else setupName
        setupFile = path / f"{fileName}{fileExtension}"
        return setupFile.open(mode, encoding="utf-8")

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
    
    @classmethod
    def WriteOperations(cls, folderPath: Path, lineNumber: int, addLineNumbers: bool, digits: int, fileExtension: str) -> int:
        for setup in cls.selected:
            lineNumber = setup.WriteOperations(folderPath, lineNumber, addLineNumbers, digits, fileExtension)
        return lineNumber