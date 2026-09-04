from __future__ import annotations
from typing import Any, Callable, ClassVar, TYPE_CHECKING

from .program import Program
from .toolpath_generation import ensure_toolpath_generated

if TYPE_CHECKING:
    from .setups.setups_context import SetupsContext

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
    _cam: Any | None = None

    @classmethod
    def load(
        cls,
        ctx: "SetupsContext",
        camSource: Any,
        programFactory: Callable[[Any], Program] = Program,
        selectedProgramName: str | None = None,
    ):
        """Loads all NCPrograms from the current document."""
        cls._cam = camSource
        cls._items = [programFactory(program) for program in camSource.ncPrograms]

        cls._current = None
        if selectedProgramName is not None:
            # Try to set the current program to the one specified in settings
            for program in cls._items:
                if program.name == selectedProgramName:
                    cls.Current = program
                    break

        ctx.load(camSource.setups)

    @classmethod
    def check_and_generate_toolpath(cls, setup):
        """Ensure that the toolpath for the given setup is generated."""
        if cls._cam is not None:
            ensure_toolpath_generated(
                setup,
                cls._cam.checkToolpath,
                cls._cam.generateToolpath,
            )
