import math


Vector3 = tuple[float, float, float]


def _dot(first: Vector3, second: Vector3) -> float:
    return sum(a * b for a, b in zip(first, second))


def _cross(first: Vector3, second: Vector3) -> Vector3:
    return (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    )


def _length(vector: Vector3) -> float:
    return math.sqrt(_dot(vector, vector))


def _normalize(vector: Vector3) -> Vector3:
    length = _length(vector)
    return tuple(value / length for value in vector)


def _projectOntoRotationPlane(vector: Vector3, axis: Vector3) -> Vector3:
    distance = _dot(axis, vector)
    return tuple(value - axis_value * distance for value, axis_value in zip(vector, axis))


def get_signed_rotation_around_axis(
    sourceDirection: Vector3,
    targetDirection: Vector3,
    rotationAxis: Vector3,
    sourceFallback: Vector3,
    targetFallback: Vector3,
    epsilon: float = 1e-6,
) -> float:
    axis = _normalize(rotationAxis)
    source = _projectOntoRotationPlane(sourceDirection, axis)
    target = _projectOntoRotationPlane(targetDirection, axis)

    if _length(source) < epsilon or _length(target) < epsilon:
        source = _projectOntoRotationPlane(sourceFallback, axis)
        target = _projectOntoRotationPlane(targetFallback, axis)
        if _length(source) < epsilon or _length(target) < epsilon:
            return 0.0

    source = _normalize(source)
    target = _normalize(target)
    sign = _dot(axis, _cross(source, target))
    alignment = _dot(source, target)
    return math.atan2(sign, alignment)
