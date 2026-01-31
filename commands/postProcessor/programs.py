from __future__ import annotations
import time

import adsk.cam

from .program import Program
from .setups import Setups
from ...lib.fusionAddInUtils.general_utils import classproperty

class _ProgramsMeta(type):
    def __iter__(cls):
        return iter(cls._items)
    def __setattr__(cls, name, value):
        # If the attribute is a classproperty with a registered setter, call it.
        desc = cls.__dict__.get(name)
        if desc is not None and hasattr(desc, 'fset') and callable(getattr(desc, 'fset')):
            desc.fset(cls, value)
            return
        return super().__setattr__(name, value)
    
class Programs(metaclass=_ProgramsMeta):
    _current: Program = None
    _items: list[Program] = []
    _cam: adsk.cam.CAM = None

    @classmethod
    def Load(cls, cam: adsk.cam.CAM):
        """Loads all NCPrograms from the current document."""
        cls._cam = cam
        cls._items = [Program(program) for program in cam.ncPrograms]
        Setups.Load(cam.setups)

    @classproperty
    def Current(cls) -> Program:
        """Returns the current NCProgram."""
        return cls._current
    
    @Current.setter
    def Current(cls, program: Program):
        """Sets the current NCProgram."""
        cls._current = program

    @classmethod
    def CheckAndGenerateToolpath(cls, setup):
        """Ensure that the toolpath for the given setup is generated."""
        if not cls._cam.checkToolpath(setup):
            genStat = cls._cam.generateToolpath(setup)
            while not genStat.isGenerationCompleted:
                time.sleep(.1)
