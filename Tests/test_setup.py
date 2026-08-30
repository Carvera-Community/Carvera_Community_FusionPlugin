from pathlib import Path
from types import SimpleNamespace

import pytest

from addin_import import import_addin_module


SetupContext = import_addin_module(
    "commands.postProcessor.setups.setup.setup_context"
).SetupContext
Setup = import_addin_module(
    "commands.postProcessor.setups.setup.setup"
).Setup


class Vector:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z


class FakeSetupAdapter:
    def origin(self, setup):
        return setup.origin

    def normal(self, setup, direction):
        return setup.normals[direction]

    def globalVector(self, direction):
        return Vector(*direction)

    def castOperation(self, value):
        return value if getattr(value, "is_operation", False) else None


class FakeOperations:
    def __init__(self, ctx, sources):
        self.sources = sources
        self.fileName = None
        self.hasHeader = False
        self.hasTail = False
        self.tools = []
        self.parse_paths = []

    def __len__(self):
        return len(self.sources)

    def parse(self, path, program):
        self.parse_paths.append((path, program))

    def set_output_path(self, path):
        self.path = path

    def set_file_extension(self, extension):
        self.extension = extension


class FakePrograms:
    Current = SimpleNamespace(disable_open_in_editor=lambda: None)
    checked = []

    @classmethod
    def check_and_generate_toolpath(cls, setup):
        cls.checked.append(setup)


def source_setup(name="Setup"):
    return SimpleNamespace(
        name=name,
        machine=None,
        isSuppressed=False,
        hasError=False,
        hasWarning=False,
        origin=SimpleNamespace(),
        normals={
            (1, 0, 0): Vector(1, 0, 0),
            (0, 1, 0): Vector(0, 1, 0),
            (0, 0, 1): Vector(0, 0, 1),
        },
        allOperations=[],
    )


def make_setup(source=None, selected=True):
    FakePrograms.checked = []
    source = source or source_setup()
    return Setup(
        SetupContext(),
        source,
        2,
        selected,
        FakeSetupAdapter(),
        FakeOperations,
        FakePrograms,
    )


def test_setup_exposes_selection_name_geometry_and_machine_state():
    setup = make_setup()

    assert setup.index == 2
    assert setup.isSelected
    assert setup.name == "Setup"
    assert setup.origin is setup.ctx.setup.origin
    assert (setup.xNormal.x, setup.yNormal.y, setup.zNormal.z) == (1, 1, 1)
    assert not setup.hasMachine


def test_setup_rename_supports_plain_prepend_and_regex():
    setup = make_setup(source_setup("Rough Setup"))

    setup.rename("", "01_", False)
    assert setup.name == "01_Rough Setup"
    setup.rename(r"Rough\s+", "Finish ", True)
    assert setup.name == "01_Finish Setup"


def test_setup_parse_casts_operations_generates_toolpath_and_parses(tmp_path):
    source = source_setup()
    first = SimpleNamespace(is_operation=True)
    ignored = SimpleNamespace(is_operation=False)
    source.allOperations = [first, ignored]
    setup = make_setup(source)

    setup.parse(tmp_path)

    assert setup.ctx.operations.sources == [first]
    assert setup.ctx.operations.parse_paths == [(tmp_path, FakePrograms.Current)]
    assert FakePrograms.checked == [source]


def test_invalid_or_unselected_setup_does_not_create_operations(tmp_path):
    setup = make_setup(selected=False)

    setup.parse(tmp_path)

    assert setup.ctx.operations is None
    assert FakePrograms.checked == []


def test_selected_setup_without_operations_stops_before_program_access(tmp_path):
    setup = make_setup()
    original_program = FakePrograms.Current
    FakePrograms.Current = None
    try:
        setup.parse(tmp_path)
    finally:
        FakePrograms.Current = original_program

    assert setup.ctx.operations.sources == []
    assert FakePrograms.checked == []


def test_setup_with_operations_requires_current_program(tmp_path):
    source = source_setup()
    source.allOperations = [SimpleNamespace(is_operation=True)]
    setup = make_setup(source)
    original_program = FakePrograms.Current
    FakePrograms.Current = None
    try:
        with pytest.raises(ValueError, match="Programs.Current is None"):
            setup.parse(tmp_path)
    finally:
        FakePrograms.Current = original_program


def test_output_path_and_extension_are_forwarded(tmp_path):
    source = source_setup()
    source.allOperations = [SimpleNamespace(is_operation=True)]
    setup = make_setup(source)
    setup.parse(tmp_path)
    output = tmp_path / "nested"

    setup.set_output_path(output)
    setup.set_file_extension(".nc")

    assert output.is_dir()
    assert setup.ctx.operations.path == output
    assert setup.ctx.operations.extension == ".nc"
