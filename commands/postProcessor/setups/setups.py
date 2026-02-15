from __future__ import annotations
from pathlib import Path
from typing import List, Iterator

import adsk.cam

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

    @classmethod
    def Load(cls, setups: adsk.cam.Setups):
        noneSelected = not any((setup.isSelected and not setup.isSuppressed and not setup.hasError for setup in setups))
        cls._items: List[Setup] = [Setup(setup, index, noneSelected) for index, setup in enumerate(setups)]

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
                signed_angle = round(first.GetRotationAroundXAxisRelativeToDeg(setup), 3)
                if signed_angle != 0:
                    needsRotation.append((setup.name, signed_angle))
                    Utils.log(f"Setups: WCS needs rotation: {signed_angle} degrees difference.")
        return (len(needsRotation) != 0, needsRotation)

    @classmethod
    def RenameAll(cls, find, replace, isRegex):
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
    
    @classproperty
    def tools(cls) -> list[adsk.cam.Tool]:
        tools = list[adsk.cam.Tool]()
        for setup in cls.selected:
            tools.extend(setup.tools)
        return tools