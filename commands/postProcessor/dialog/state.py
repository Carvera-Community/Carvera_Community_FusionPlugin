from typing import Any


def is_output_name_valid(file_name: str, numeric_name: bool) -> bool:
    return bool(file_name) and (not numeric_name or file_name.isnumeric())


def numeric_name_digits(file_name: str | None, maximum: int = 6) -> int | None:
    if file_name is None or not file_name.isnumeric():
        return None
    return min(len(file_name), maximum)


def is_setup_selectable(
    *,
    has_reference: bool,
    valid_program: bool,
    same_origin: bool,
    parallel_x_axis: bool,
    can_rotate: bool,
    required_rotation: float,
    machine_has_a_axis: bool,
) -> bool:
    if not has_reference:
        return True
    return (
        same_origin
        and parallel_x_axis
        and valid_program
        and (
            required_rotation == 0
            or (machine_has_a_axis and can_rotate)
        )
    )


def can_process(program: Any | None, context: Any) -> bool:
    if program is None or not program.hasMachine or not context.hasSelected:
        return False
    if any(setup.ctx.hasError for setup in context.selected):
        return False
    if program.machine_has_a_axis:
        return True

    from ..setups.setups import a_axis_rotation_required

    return not a_axis_rotation_required(context)[0]
