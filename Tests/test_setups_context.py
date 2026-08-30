from pathlib import Path
from types import SimpleNamespace

from addin_import import import_addin_module


SetupsContext = import_addin_module(
    "commands.postProcessor.setups.setups_context"
).SetupsContext
Settings = import_addin_module(
    "commands.postProcessor.settings.settings"
).Settings
Constants = import_addin_module(
    "commands.postProcessor.settings.constants"
).Constants


class FakeSetup:
    def __init__(self, ctx, source, index, selected):
        self.ctx = ctx
        self.ctx.setup = source
        self.ctx.index = index
        self.ctx.is_selected = selected
        self.index = index
        self.name = source.name
        self.is_selected = selected
        self.tools = list(source.tools)
        self.parse_paths = []
        self.rename_calls = []

    def parse(self, path):
        self.parse_paths.append(path)

    def rename(self, find, replace, is_regex):
        self.rename_calls.append((find, replace, is_regex))

    def set_output_path(self, path):
        self.outputPath = path

    def set_file_extension(self, extension):
        self.extension = extension


def source(name, selected=False, suppressed=False, error=False, tools=()):
    return SimpleNamespace(
        name=name,
        isSelected=selected,
        isSuppressed=suppressed,
        hasError=error,
        hasWarning=False,
        tools=tools,
    )


def context_with(sources):
    context = SetupsContext()
    context.load(sources, FakeSetup)
    return context


def test_context_instances_do_not_share_setup_collections():
    first = SetupsContext()
    second = SetupsContext()

    first._items.append(object())

    assert second._items == []


def configure_paths(grouping, **overrides):
    values = {
        Settings.FLAT_FILE_STRUCTURE: False,
        Settings.NUMERIC_NAME: False,
        Settings.OPERATIONS_GROUPING: grouping,
        Settings.FILE_SEQUENCE: False,
        Settings.FILE_SEQUENCE_DIGITS: 3,
    }
    values.update(overrides)
    Settings._items = values


def test_load_selects_all_valid_setups_when_none_was_selected():
    context = context_with(
        [source("First"), source("Invalid", suppressed=True), source("Second")]
    )

    assert [setup.name for setup in context.selected] == ["First", "Second"]
    assert context.has_selected


def test_load_preserves_explicit_selection():
    context = context_with([source("First"), source("Second", selected=True)])

    assert [setup.name for setup in context.selected] == ["Second"]


def test_tools_are_collected_from_selected_setups():
    first_tool, second_tool = object(), object()
    context = context_with(
        [source("First", tools=[first_tool]), source("Second", tools=[second_tool])]
    )

    assert context.tools == [first_tool, second_tool]


def test_parse_visits_selected_setups(tmp_path):
    context = context_with([source("First"), source("Second")])

    context.parse(tmp_path)

    assert [setup.parse_paths for setup in context.selected] == [[tmp_path], [tmp_path]]


def test_rename_can_target_selected_or_all_setups():
    context = context_with([source("First"), source("Second", selected=True)])

    context.rename_setups("x", "y", False, onlySelected=True)
    assert context._items[0].rename_calls == []
    assert context._items[1].rename_calls == [("x", "y", False)]

    context.rename_setups("a", "b", True, onlySelected=False)
    assert context._items[0].rename_calls == [("a", "b", True)]


def test_output_path_file_name_and_extension_are_forwarded(tmp_path):
    context = context_with([source("First Setup")])
    operations = SimpleNamespace(file_name=None)
    context.selected[0].ctx.operations = operations
    context.selected[0].ctx.set_file_name = lambda name: setattr(operations, "file_name", name)
    configure_paths(Constants.OperationsGroupings.PER_OPERATION)

    context.set_path(tmp_path, lambda name: name.replace(" ", "_"))
    context.set_file_name("job")
    context.set_file_extension(".nc")

    assert context.selected[0].outputPath == tmp_path / "First_Setup"
    assert operations.file_name == "job"
    assert context.selected[0].extension == ".nc"
