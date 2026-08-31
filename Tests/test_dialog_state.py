from types import SimpleNamespace

from addin_import import import_addin_module


state = import_addin_module("commands.postProcessor.dialog.state")


def test_output_name_validation_handles_required_and_numeric_names():
    assert state.is_output_name_valid("job", numeric_name=False)
    assert state.is_output_name_valid("0012", numeric_name=True)
    assert not state.is_output_name_valid("", numeric_name=False)
    assert not state.is_output_name_valid("job", numeric_name=True)


def test_numeric_name_digits_are_bounded():
    assert state.numeric_name_digits("0012") == 4
    assert state.numeric_name_digits("00000001") == 6
    assert state.numeric_name_digits("job") is None


def test_output_folder_validation_requires_an_existing_directory(tmp_path):
    assert state.is_output_folder_valid(str(tmp_path))
    assert not state.is_output_folder_valid(str(tmp_path / "missing"))
    assert not state.is_output_folder_valid("")

    file_path = tmp_path / "file.nc"
    file_path.write_text("", encoding="utf-8")
    assert not state.is_output_folder_valid(str(file_path))


def test_combine_tools_is_only_available_for_setup_and_tool_grouping():
    groupings = import_addin_module(
        "commands.postProcessor.settings.constants"
    ).Constants.OperationsGroupings
    available = [
        grouping
        for grouping in groupings
        if state.can_combine_tools(grouping, groupings)
    ]

    assert available == [groupings.SETUP_AND_TOOL]


def test_first_setup_is_selectable_without_reference_program():
    assert state.is_setup_selectable(
        has_reference=False,
        valid_program=False,
        same_origin=False,
        parallel_x_axis=False,
        can_rotate=False,
        required_rotation=90,
        machine_has_a_axis=False,
    )


def test_rotated_setup_requires_aligned_axes_and_rotary_machine():
    base = dict(
        has_reference=True,
        valid_program=True,
        same_origin=True,
        parallel_x_axis=True,
        can_rotate=True,
        required_rotation=90,
    )

    assert state.is_setup_selectable(**base, machine_has_a_axis=True)
    assert not state.is_setup_selectable(**base, machine_has_a_axis=False)
    assert not state.is_setup_selectable(
        **{**base, "same_origin": False},
        machine_has_a_axis=True,
    )


def test_process_validation_rejects_missing_machine_selection_and_errors():
    context = SimpleNamespace(has_selected=True, selected=[])
    assert not state.can_process(None, context)
    assert not state.can_process(
        SimpleNamespace(has_machine=False, machine_has_a_axis=True),
        context,
    )

    context.selected = [SimpleNamespace(ctx=SimpleNamespace(has_error=True))]
    assert not state.can_process(
        SimpleNamespace(has_machine=True, machine_has_a_axis=True),
        context,
    )


def test_rotary_machine_can_process_valid_selected_setups():
    context = SimpleNamespace(
        has_selected=True,
        selected=[SimpleNamespace(ctx=SimpleNamespace(has_error=False))],
    )
    program = SimpleNamespace(has_machine=True, machine_has_a_axis=True)

    assert state.can_process(program, context)
