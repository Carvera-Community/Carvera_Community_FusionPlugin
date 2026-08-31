from types import SimpleNamespace

from addin_import import import_addin_module


table = import_addin_module("commands.postProcessor.dialog.layout.setup_table")


def setup(selected=True):
    return SimpleNamespace(index=3, name="Side", is_selected=selected)


def test_reference_row_reports_alignment_and_rotation():
    state = table.get_row_state(
        setup(),
        has_reference=True,
        valid_program=True,
        same_origin=True,
        parallel_x_axis=True,
        can_rotate=True,
        rotation=90,
        machine_has_a_axis=True,
    )

    assert state == {
        table.INDEX: 3,
        table.NAME: "Side",
        table.ENABLED: True,
        table.SELECTED: True,
        table.ORIGIN: "Same",
        table.X_NORMAL: "Aligned",
        table.ROTATION: "90°",
    }


def test_ineligible_row_is_disabled_and_deselected():
    state = table.get_row_state(
        setup(),
        has_reference=True,
        valid_program=True,
        same_origin=False,
        parallel_x_axis=True,
        can_rotate=True,
        rotation=0,
        machine_has_a_axis=True,
    )

    assert not state[table.ENABLED]
    assert not state[table.SELECTED]
    assert state[table.ORIGIN] == "Different"


def test_first_selected_setup_is_rendered_as_reference():
    state = table.get_row_state(
        setup(),
        has_reference=False,
        valid_program=False,
        same_origin=False,
        parallel_x_axis=False,
        can_rotate=False,
        rotation=0,
        machine_has_a_axis=False,
    )

    assert state[table.ENABLED]
    assert state[table.ORIGIN] == "(reference)"
    assert state[table.X_NORMAL] == "(reference)"
    assert state[table.ROTATION] == "(reference)"
