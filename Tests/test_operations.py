from types import SimpleNamespace

from addin_import import import_addin_module


OperationsContext = import_addin_module(
    "commands.postProcessor.operations.operations_context"
).OperationsContext
Operations = import_addin_module(
    "commands.postProcessor.operations.operations"
).Operations
Settings = import_addin_module(
    "commands.postProcessor.settings.settings"
).Settings
ProcessingSettings = import_addin_module(
    "commands.postProcessor.processing_settings"
).ProcessingSettings


class FakeFusionAdapter:
    def get_tool_number(self, operation):
        return operation.toolNumber

    def max_filename_length(self):
        return 255


def source(name, tool_number=None, suppressed=False):
    return SimpleNamespace(
        name=name,
        toolNumber=tool_number,
        isSuppressed=suppressed,
        hasToolpath=tool_number is not None,
        tool=SimpleNamespace(number=tool_number),
    )


def make_operations(sources, combine=False):
    Settings._items = dict(Settings._default_settings)
    Settings._items[Settings.COMBINE_TOOL] = combine
    return Operations(
        OperationsContext(processingSettings=ProcessingSettings.capture()),
        sources,
        FakeFusionAdapter(),
    )


def test_operations_builds_domain_groups_from_sources():
    operations = make_operations(
        [source("Rough", 1), source("Manual"), source("Finish", 2)]
    )

    assert len(operations) == 2
    assert [operation.name for operation in operations] == [
        "Rough-Manual",
        "Finish",
    ]
    assert [operation.toolId for operation in operations] == [1, 2]


def test_operations_combines_consecutive_same_tool_when_enabled():
    operations = make_operations(
        [source("Rough", 1), source("Finish", 1)],
        combine=True,
    )

    assert len(operations) == 1
    assert operations[0].name == "Rough-Finish"


def test_operations_uses_captured_grouping_setting():
    Settings._items = dict(Settings._default_settings)
    Settings._items[Settings.COMBINE_TOOL] = True
    snapshot = ProcessingSettings.capture()
    Settings._items[Settings.COMBINE_TOOL] = False

    operations = Operations(
        OperationsContext(processingSettings=snapshot),
        [source("Rough", 1), source("Finish", 1)],
        FakeFusionAdapter(),
    )

    assert len(operations) == 1


def test_operations_exposes_unique_tools_in_source_order():
    first_tool = SimpleNamespace(number=1)
    second_tool = SimpleNamespace(number=2)
    sources = [source("One", 1), source("Two", 2), source("Three", 1)]
    sources[0].tool = first_tool
    sources[1].tool = second_tool
    sources[2].tool = first_tool
    operations = make_operations(sources)

    assert operations.tools == [first_tool, second_tool]


def test_parse_records_first_tail_operation(tmp_path):
    operations = make_operations([source("One", 1), source("Two", 2)])
    program = object()
    calls = []
    for index, operation in enumerate(operations):
        operation.parse = lambda path, active_program: calls.append((path, active_program))
        operation.ctx.tailStartLine = 8 if index == 0 else -1

    operations.parse(tmp_path, program)

    assert calls == [(tmp_path, program), (tmp_path, program)]
    assert operations.ctx.operationWithTail is operations[0]
