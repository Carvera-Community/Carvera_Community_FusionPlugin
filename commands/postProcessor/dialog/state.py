from pathlib import Path
import re
from typing import Any


def is_output_name_valid(file_name: str, numeric_name: bool) -> bool:
    return bool(file_name) and (not numeric_name or file_name.isnumeric())


def is_output_folder_valid(folder: str) -> bool:
    return bool(folder.strip()) and Path(folder).expanduser().is_dir()


def can_combine_tools(grouping: Any, operations_groupings: Any) -> bool:
    return grouping == operations_groupings.SETUP_AND_TOOL


def is_find_pattern_valid(pattern: str, use_regex: bool) -> bool:
    if not use_regex:
        return True
    try:
        re.compile(pattern)
    except re.error:
        return False
    return True


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
    if program is None or not program.has_machine or not context.has_selected:
        return False
    if any(setup.ctx.has_error for setup in context.selected):
        return False
    if program.machine_has_a_axis:
        return True

    from ..setups.setups import a_axis_rotation_required

    return not a_axis_rotation_required(context)[0]
