from typing import Final, TypeVar, cast
from adsk import cam
from ...lib.fusionParameters.cast_cam_param import castCAMParam

T = TypeVar("T", int, float, bool, str)

class Parameters:
    """The CAM parameters of the Fusion NCProgram."""
    def __init__(self, parameters: cam.CAMParameters):
        self._parameters = parameters

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
        
        if t is int:
            return cast(T, castCAMParam.ToInt(param))
        if t is float:
            return cast(T, castCAMParam.ToFloat(param))
        if t is bool:
            return cast(T, castCAMParam.ToBool(param))
        if t is str:
            return cast(T, castCAMParam.ToStr(param))
        raise TypeError(f"Unhandled type '{T}' of parameter '{name}'")
    
    def Set(self, name: str, value: T) -> None:
        """Sets the value of the NCParameter with the given name."""
        param = self._parameters.itemByName(name)

        if isinstance(value, bool):
            boolValue = cam.BooleanParameterValue.cast(param.value)
            if boolValue is None:
                raise TypeError(f"{name} is not bool")
            boolValue.value = value
        elif isinstance(value, int):
            intValue = cam.IntegerParameterValue.cast(param.value)
            if intValue is None:
                raise TypeError(f"{name} is not int")
            intValue.value = value
        elif isinstance(value, float):
            floatValue = cam.FloatParameterValue.cast(param.value)
            if floatValue is None:
                raise TypeError(f"{name} is not float")
            floatValue.value = value
        elif isinstance(value, str):
            strValue = cam.StringParameterValue.cast(param.value)
            if strValue is None:
                raise TypeError(f"{name} is not str")
            strValue.value = value
        else:
            raise TypeError(f"Type {typeof(value)} is not handled")