from typing import Any, Final, Protocol, TypeVar, cast

T = TypeVar("T", int, float, bool, str)


class ParameterCollection(Protocol):
    def itemByName(self, name: str): ...


class ParameterValueAdapter(Protocol):
    def get(self, parameter, valueType: type[T]) -> T: ...
    def set(self, parameter, value: Any) -> None: ...

class Parameters:
    """The CAM parameters of the Fusion NCProgram."""
    def __init__(
        self,
        parameters: ParameterCollection,
        valueAdapter: ParameterValueAdapter | None = None,
    ):
        self._parameters = parameters
        if valueAdapter is None:
            from .fusion_adapters.parameter_values import FusionParameterValueAdapter

            valueAdapter = FusionParameterValueAdapter()
        self._valueAdapter = valueAdapter

    FILE_NAME: Final      = 'nc_program_filename'
    OPEN_IN_EDITOR: Final = 'nc_program_openInEditor'
    OUTPUT_FOLDER: Final  = 'nc_program_output_folder'
    NAME: Final           = 'nc_program_name'
    EXTENSION: Final      = 'nc_program_nc_extension'

    def Get(self, name: str, t: type[T]) -> T | None:
        """Returns the value of the NCParameter with the given name, or None if it does not exist."""
        param = self._parameters.itemByName(name)
        if param is None:
            return None
        
        if t not in (int, float, bool, str):
            raise TypeError(f"Unhandled type '{t}' of parameter '{name}'")
        return cast(T, self._valueAdapter.get(param, t))
    
    def Set(self, name: str, value: T) -> None:
        """Sets the value of the NCParameter with the given name."""
        param = self._parameters.itemByName(name)

        if param is None:
            raise KeyError(f"Parameter '{name}' does not exist")
        self._valueAdapter.set(param, value)
