from __future__ import annotations
import time
from typing import TYPE_CHECKING, ClassVar, Optional

from adsk import cam
from adsk.cam import Setup as adskSetup

from .program import Program
from .setups.setups_context import SetupsContext
from .settings.settings import Settings
from ...lib.fusionAddInUtils.general_utils import classproperty

class _ProgramsMeta(type):
    # Just to help Pylance to understand the code.
    _items: ClassVar[list[Program]]
    _current: Program | None

    def __iter__(cls):
        return iter(cls._items)

    def __setattr__(cls, name, value):
        # If the attribute is a classproperty with a registered setter, call it.
        desc = cls.__dict__.get(name)
        if desc is not None and hasattr(desc, 'fset') and callable(getattr(desc, 'fset')):
            desc.fset(cls, value)
            return
        return super().__setattr__(name, value)

    @property
    def Current(cls) -> Program | None:
        return cls._current
    
    @Current.setter
    def Current(cls, value: Program | None) -> None:
        cls._current = value
    
class Programs(metaclass=_ProgramsMeta):
    _current: Program | None = None
    _items: list[Program] = []
    _cam: cam.CAM | None = None

    @classmethod
    def Load(cls, ctx: SetupsContext, cam: cam.CAM):
        """Loads all NCPrograms from the current document."""
        cls._cam = cam
        cls._items = [Program(program) for program in cam.ncPrograms]

        cls._current = None
        if Settings(Settings.NC_PROGRAM) is not None:
            # Try to set the current program to the one specified in settings
            for program in cls._items:
                if program.name == Settings(Settings.NC_PROGRAM):
                    cls.Current = program
                    break

        ctx.load(cam.setups)

    @classmethod
    def CheckAndGenerateToolpath(cls, setup: adskSetup):
        """Ensure that the toolpath for the given setup is generated."""
        if cls._cam is not None and not cls._cam.checkToolpath(setup):
            genStat = cls._cam.generateToolpath(setup)
            while not genStat.isGenerationCompleted:
                time.sleep(.1)
