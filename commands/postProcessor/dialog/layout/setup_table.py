from typing import Any

from ...strings import Strings
from ..state import is_setup_selectable


INDEX = "index"
ENABLED = "enabled"
SELECTED = "selected"
NAME = "name"
ORIGIN = "origin"
X_NORMAL = "xNormal"
ROTATION = "rotation"


def get_row_state(
    setup: Any,
    *,
    has_reference: bool,
    valid_program: bool,
    same_origin: bool,
    parallel_x_axis: bool,
    can_rotate: bool,
    rotation: float,
    machine_has_a_axis: bool,
) -> dict[str, Any]:
    selectable = is_setup_selectable(
        has_reference=has_reference,
        valid_program=valid_program,
        same_origin=same_origin,
        parallel_x_axis=parallel_x_axis,
        can_rotate=can_rotate,
        required_rotation=rotation,
        machine_has_a_axis=machine_has_a_axis,
    )
    selected = setup.is_selected if selectable else False

    if has_reference:
        origin_text = Strings("Same") if same_origin else Strings("Different")
        x_normal_text = Strings("Aligned") if parallel_x_axis else Strings("Misaligned")
        rotation_text = f"{rotation}°" if parallel_x_axis else ""
    else:
        origin_text = x_normal_text = rotation_text = (
            Strings("(reference)") if selected else "-"
        )

    return {
        INDEX: setup.index,
        NAME: setup.name,
        ENABLED: selectable,
        SELECTED: selected,
        ORIGIN: origin_text,
        X_NORMAL: x_normal_text,
        ROTATION: rotation_text,
    }


def apply_row_state(inputs: Any, row_state: dict[str, Any]) -> None:
    from adsk.core import BoolValueCommandInput, StringValueCommandInput

    index = row_state[INDEX]
    checkbox = BoolValueCommandInput.cast(inputs.itemById(f"setupSelected_{index}"))
    name = StringValueCommandInput.cast(inputs.itemById(f"setupName_{index}"))
    origin = StringValueCommandInput.cast(inputs.itemById(f"setupOrigin_{index}"))
    x_normal = StringValueCommandInput.cast(inputs.itemById(f"setupXNormal_{index}"))
    rotation = StringValueCommandInput.cast(inputs.itemById(f"setupARotation_{index}"))

    checkbox.isEnabled = row_state[ENABLED]
    name.value = row_state[NAME]
    name.isEnabled = row_state[ENABLED]
    origin.isEnabled = row_state[ENABLED]
    x_normal.isEnabled = row_state[ENABLED]
    rotation.isEnabled = row_state[ENABLED]

    checkbox.value = row_state[SELECTED]
    origin.value = row_state[ORIGIN]
    x_normal.value = row_state[X_NORMAL]
    rotation.value = row_state[ROTATION]
