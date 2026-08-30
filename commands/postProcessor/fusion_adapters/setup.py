from adsk import cam
from adsk.core import Point3D, Vector3D

from ..operations.operation_source import OperationSource
from ..setups.setup_source import SetupSource, raw_setup
from ....lib.fusionParameters.cast_cam_param import castCAMParam


class FusionSetupAdapter:
    def snapshot_setup(self, setup):
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

    def rename_setup(self, setup, name: str) -> None:
        raw_setup(setup).name = name
        setup.name = name

    def origin(self, setup):
        setup = raw_setup(setup)
        origin = Point3D.create(0, 0, 0)
        origin.transformBy(setup.workCoordinateSystem)
        return origin

    def normal(self, setup, direction: tuple[float, float, float]):
        setup = raw_setup(setup)
        vector = Vector3D.create(*direction)
        vector.transformBy(setup.workCoordinateSystem)
        vector.normalize()
        return vector

    def global_vector(self, direction: tuple[float, float, float]):
        return Vector3D.create(*direction)

    def cast_operation(self, value):
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
