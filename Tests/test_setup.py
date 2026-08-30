from pathlib import Path
from types import SimpleNamespace

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

    def Parse(self, path):
        self.parse_paths.append(path)

    def SetOutputPath(self, path):
        self.path = path

    def SetFileExtension(self, extension):
        self.extension = extension


class FakePrograms:
    Current = SimpleNamespace(DisableOpenInEditor=lambda: None)
    checked = []

    @classmethod
    def CheckAndGenerateToolpath(cls, setup):
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

    setup.Rename("", "01_", False)
    assert setup.name == "01_Rough Setup"
    setup.Rename(r"Rough\s+", "Finish ", True)
    assert setup.name == "01_Finish Setup"


def test_setup_parse_casts_operations_generates_toolpath_and_parses(tmp_path):
    source = source_setup()
    first = SimpleNamespace(is_operation=True)
    ignored = SimpleNamespace(is_operation=False)
    source.allOperations = [first, ignored]
    setup = make_setup(source)

    setup.Parse(tmp_path)

    assert setup.ctx.operations.sources == [first]
    assert setup.ctx.operations.parse_paths == [tmp_path]
    assert FakePrograms.checked == [source]


def test_invalid_or_unselected_setup_does_not_create_operations(tmp_path):
    setup = make_setup(selected=False)

    setup.Parse(tmp_path)

    assert setup.ctx.operations is None
    assert FakePrograms.checked == []


def test_output_path_and_extension_are_forwarded(tmp_path):
    source = source_setup()
    source.allOperations = [SimpleNamespace(is_operation=True)]
    setup = make_setup(source)
    setup.Parse(tmp_path)
    output = tmp_path / "nested"

    setup.SetOutputPath(output)
    setup.SetFileExtension(".nc")

    assert output.is_dir()
    assert setup.ctx.operations.path == output
    assert setup.ctx.operations.extension == ".nc"
