from types import SimpleNamespace

from addin_import import import_addin_module


programs_module = import_addin_module("commands.postProcessor.programs")
Programs = programs_module.Programs


class FakeContext:
    def __init__(self):
        self.loaded = None

    def load(self, setups):
        self.loaded = setups


def reset_programs():
    Programs._items = []
    Programs._current = None
    Programs._cam = None


def test_load_wraps_programs_selects_saved_name_and_loads_setups():
    reset_programs()
    sources = [SimpleNamespace(name="First"), SimpleNamespace(name="Second")]
    setups = [object()]
    cam_source = SimpleNamespace(ncPrograms=sources, setups=setups)
    context = FakeContext()

    Programs.load(context, cam_source, lambda source: source, "Second")

    assert list(Programs) == sources
    assert Programs.Current is sources[1]
    assert context.loaded == setups


def test_load_leaves_current_empty_when_saved_program_is_missing():
    reset_programs()
    source = SimpleNamespace(name="First")

    Programs.load(
        FakeContext(),
        SimpleNamespace(ncPrograms=[source], setups=[]),
        lambda item: item,
        "Missing",
    )

    assert Programs.Current is None


def test_toolpath_check_is_skipped_without_cam_source():
    reset_programs()

    Programs.check_and_generate_toolpath(object())
