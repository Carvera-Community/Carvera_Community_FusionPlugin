from adsk.cam import CAMParameter
from .cast_param import castParam

class castCAMParam:
    @staticmethod
    def ToInt(param: CAMParameter) -> int:
        try:
            return castParam.ToInt(param.value)
        except TypeError:
            raise TypeError(f"Parameter '{param.name}' is not an int")

    @staticmethod
    def ToFloat(param: CAMParameter) -> float:
        try:
            return castParam.ToFloat(param.value)
        except TypeError:
            raise TypeError(f"Parameter '{param.name}' is not float")

    @staticmethod
    def ToBool(param: CAMParameter) -> bool:
        try:
            return castParam.ToBool(param.value)
        except TypeError:
            raise TypeError(f"Parameter '{param.name}' is not bool")

    @staticmethod
    def ToStr(param: CAMParameter) -> str:
        try:
            return castParam.ToStr(param.value)
        except TypeError:
            raise TypeError(f"Parameter '{param.name}' is not str")
