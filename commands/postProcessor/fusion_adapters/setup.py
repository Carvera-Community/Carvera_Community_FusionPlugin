from adsk import cam
from adsk.core import Point3D, Vector3D


class FusionSetupAdapter:
    def origin(self, setup):
        origin = Point3D.create(0, 0, 0)
        origin.transformBy(setup.workCoordinateSystem)
        return origin

    def normal(self, setup, direction: tuple[float, float, float]):
        vector = Vector3D.create(*direction)
        vector.transformBy(setup.workCoordinateSystem)
        vector.normalize()
        return vector

    def globalVector(self, direction: tuple[float, float, float]):
        return Vector3D.create(*direction)

    def castOperation(self, value):
        return cam.Operation.cast(value)
