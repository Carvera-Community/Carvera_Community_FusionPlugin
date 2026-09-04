from adsk.cam import (
    ParameterValue,
    IntegerParameterValue, 
    BooleanParameterValue, 
    StringParameterValue,
    FloatParameterValue
)

class castParam:
    @staticmethod
    def ToInt(param: ParameterValue) -> int:
        integerParameter = IntegerParameterValue.cast(param)
        if integerParameter is None:
            raise TypeError()
        return integerParameter.value

    @staticmethod
    def ToFloat(param: ParameterValue) -> float:
        floatParameter = FloatParameterValue.cast(param)
        if floatParameter is None:
            raise TypeError()
        return floatParameter.value

    @staticmethod
    def ToBool(param: ParameterValue) -> bool:
        boolParameter = BooleanParameterValue.cast(param)
        if boolParameter is None:
            raise TypeError()
        return boolParameter.value

    @staticmethod
    def ToStr(param: ParameterValue) -> str:
        strParameter = StringParameterValue.cast(param)
        if strParameter is None:
            raise TypeError()
        return strParameter.value
