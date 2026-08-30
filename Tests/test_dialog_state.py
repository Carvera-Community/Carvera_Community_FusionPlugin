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
    context = SimpleNamespace(hasSelected=True, selected=[])
    assert not state.can_process(None, context)
    assert not state.can_process(
        SimpleNamespace(hasMachine=False, machineHasAAxis=True),
        context,
    )

    context.selected = [SimpleNamespace(ctx=SimpleNamespace(hasError=True))]
    assert not state.can_process(
        SimpleNamespace(hasMachine=True, machineHasAAxis=True),
        context,
    )


def test_rotary_machine_can_process_valid_selected_setups():
    context = SimpleNamespace(
        hasSelected=True,
        selected=[SimpleNamespace(ctx=SimpleNamespace(hasError=False))],
    )
    program = SimpleNamespace(hasMachine=True, machineHasAAxis=True)

    assert state.can_process(program, context)
