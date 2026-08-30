from adsk import cam
from adsk.core import Point3D, Vector3D

from ..operations.operation_source import OperationSource
from ..setups.setup_source import SetupSource, rawSetup
from ....lib.fusionParameters.cast_cam_param import castCAMParam


class FusionSetupAdapter:
    def snapshotSetup(self, setup):
        return SetupSource(
            raw=setup,
            name=setup.name,
            isSelected=setup.isSelected,
            isSuppressed=setup.isSuppressed,
            hasError=setup.hasError,
            hasWarning=setup.hasWarning,
            machine=setup.machine,
            allOperations=tuple(setup.allOperations),
        )

    def renameSetup(self, setup, name: str) -> None:
        rawSetup(setup).name = name
        setup.name = name

    def origin(self, setup):
        setup = rawSetup(setup)
        origin = Point3D.create(0, 0, 0)
        origin.transformBy(setup.workCoordinateSystem)
        return origin

    def normal(self, setup, direction: tuple[float, float, float]):
        setup = rawSetup(setup)
        vector = Vector3D.create(*direction)
        vector.transformBy(setup.workCoordinateSystem)
        vector.normalize()
        return vector

    def globalVector(self, direction: tuple[float, float, float]):
        return Vector3D.create(*direction)

    def castOperation(self, value):
        operation = cam.Operation.cast(value)
        if operation is None:
            return None
        tool = operation.tool if operation.hasToolpath else None
        return OperationSource(
            raw=operation,
            name=operation.name,
            isSuppressed=operation.isSuppressed,
            hasToolpath=operation.hasToolpath,
            tool=tool,
            toolNumber=(
                castCAMParam.ToInt(tool.parameters.itemByName("tool_number"))
                if tool is not None
                else None
            ),
        )
