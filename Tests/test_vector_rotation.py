import math

import pytest

from addin_import import import_addin_module


rotation = import_addin_module(
    "commands.postProcessor.setups.setup.vector_rotation"
)
getSignedRotationAroundAxis = rotation.getSignedRotationAroundAxis


X_AXIS = (1.0, 0.0, 0.0)
Y_AXIS = (0.0, 1.0, 0.0)
Z_AXIS = (0.0, 0.0, 1.0)


def angle(source, target, source_fallback=Y_AXIS, target_fallback=Y_AXIS):
    return getSignedRotationAroundAxis(
        sourceDirection=source,
        targetDirection=target,
        rotationAxis=X_AXIS,
        sourceFallback=source_fallback,
        targetFallback=target_fallback,
    )


def test_parallel_directions_have_zero_rotation():
    assert angle(Z_AXIS, Z_AXIS) == pytest.approx(0.0)


def test_positive_quarter_turn_uses_right_hand_rule():
    assert angle(Z_AXIS, (0.0, -1.0, 0.0)) == pytest.approx(math.pi / 2)


def test_negative_quarter_turn_uses_right_hand_rule():
    assert angle(Z_AXIS, Y_AXIS) == pytest.approx(-math.pi / 2)


def test_opposite_directions_produce_half_turn():
    assert abs(angle(Z_AXIS, (0.0, 0.0, -1.0))) == pytest.approx(math.pi)


def test_non_unit_rotation_axis_is_normalized():
    result = getSignedRotationAroundAxis(
        sourceDirection=Z_AXIS,
        targetDirection=(0.0, -1.0, 0.0),
        rotationAxis=(2.0, 0.0, 0.0),
        sourceFallback=Y_AXIS,
        targetFallback=Z_AXIS,
    )

    assert result == pytest.approx(math.pi / 2)


def test_direction_parallel_to_axis_uses_fallback_vectors():
    assert angle(
        X_AXIS,
        X_AXIS,
        source_fallback=Y_AXIS,
        target_fallback=Z_AXIS,
    ) == pytest.approx(math.pi / 2)


def test_fully_degenerate_input_returns_zero():
    assert angle(
        X_AXIS,
        X_AXIS,
        source_fallback=X_AXIS,
        target_fallback=X_AXIS,
    ) == 0.0
