from typing import Any

from adsk import cam

from ....lib.fusionParameters.cast_cam_param import castCAMParam


class FusionParameterValueAdapter:
    def get(self, parameter, valueType: type):
        if valueType is int:
            return castCAMParam.ToInt(parameter)
        if valueType is float:
            return castCAMParam.ToFloat(parameter)
        if valueType is bool:
            return castCAMParam.ToBool(parameter)
        if valueType is str:
            return castCAMParam.ToStr(parameter)
        raise TypeError(f"Unhandled parameter type '{valueType}'")

    def set(self, parameter, value: Any) -> None:
        if isinstance(value, bool):
            typedValue = cam.BooleanParameterValue.cast(parameter.value)
        elif isinstance(value, int):
            typedValue = cam.IntegerParameterValue.cast(parameter.value)
        elif isinstance(value, float):
            typedValue = cam.FloatParameterValue.cast(parameter.value)
        elif isinstance(value, str):
            typedValue = cam.StringParameterValue.cast(parameter.value)
        else:
            raise TypeError(f"Type {type(value)} is not handled")

        if typedValue is None:
            raise TypeError(f"{parameter.name} is not {type(value).__name__}")
        typedValue.value = value
