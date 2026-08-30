from types import SimpleNamespace

from addin_import import import_addin_module


programs_module = import_addin_module("commands.postProcessor.programs")
Programs = programs_module.Programs
Settings = import_addin_module(
    "commands.postProcessor.settings.settings"
).Settings


class FakeContext:
    def __init__(self):
        self.loaded = None

    def load(self, setups):
        self.loaded = setups


def reset_programs():
    Programs._items = []
    Programs._current = None
    Programs._cam = None
    Settings._items = {}


def test_load_wraps_programs_selects_saved_name_and_loads_setups():
    reset_programs()
    Settings.Set(Settings.NC_PROGRAM, "Second")
    sources = [SimpleNamespace(name="First"), SimpleNamespace(name="Second")]
    setups = [object()]
    cam_source = SimpleNamespace(ncPrograms=sources, setups=setups)
    context = FakeContext()

    Programs.Load(context, cam_source, lambda source: source)

    assert list(Programs) == sources
    assert Programs.Current is sources[1]
    assert context.loaded == setups


def test_load_leaves_current_empty_when_saved_program_is_missing():
    reset_programs()
    Settings.Set(Settings.NC_PROGRAM, "Missing")
    source = SimpleNamespace(name="First")

    Programs.Load(
        FakeContext(),
        SimpleNamespace(ncPrograms=[source], setups=[]),
        lambda item: item,
    )

    assert Programs.Current is None


def test_toolpath_check_is_skipped_without_cam_source():
    reset_programs()

    Programs.CheckAndGenerateToolpath(object())
