from adsk import cam

from ....lib.fusionAddInUtils.general_utils import Utils
from ....lib.fusionParameters.cast_cam_param import castCAMParam


class FusionOperationAdapter:
    def castOperation(self, value):
        return cam.Operation.cast(value)

    def getToolNumber(self, operation) -> int:
        if hasattr(operation, "toolNumber"):
            return operation.toolNumber
        return castCAMParam.ToInt(
            operation.tool.parameters.itemByName("tool_number")
        )

    def maxFilenameLength(self) -> int:
        return Utils.maxFilenameLength()
