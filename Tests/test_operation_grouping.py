from dataclasses import dataclass

from addin_import import import_addin_module


grouping = import_addin_module(
    "commands.postProcessor.operations.operation_grouping"
)
groupOperationSources = grouping.groupOperationSources


@dataclass
class FakeSourceOperation:
    name: str
    toolNumber: int | None = None
    isSuppressed: bool = False

    @property
    def hasToolpath(self) -> bool:
        return self.toolNumber is not None


def group(operations, combine=False):
    return groupOperationSources(
        operations,
        combineTool=combine,
        getToolNumber=lambda operation: operation.toolNumber,
    )


def names(groups):
    return [
        [item.source.name for item in operation_group]
        for operation_group in groups
    ]


def indices(groups):
    return [
        [item.index for item in operation_group]
        for operation_group in groups
    ]


def test_empty_input_produces_no_groups():
    assert group([]) == []


def test_toolpath_operations_are_separate_by_default():
    operations = [
        FakeSourceOperation("Rough", 1),
        FakeSourceOperation("Finish", 1),
    ]

    assert names(group(operations)) == [["Rough"], ["Finish"]]


def test_consecutive_same_tool_operations_can_be_combined():
    operations = [
        FakeSourceOperation("Rough", 1),
        FakeSourceOperation("Finish", 1),
        FakeSourceOperation("Drill", 2),
    ]

    assert names(group(operations, combine=True)) == [
        ["Rough", "Finish"],
        ["Drill"],
    ]


def test_same_tool_is_not_combined_across_another_tool():
    operations = [
        FakeSourceOperation("First T1", 1),
        FakeSourceOperation("T2", 2),
        FakeSourceOperation("Second T1", 1),
    ]

    assert names(group(operations, combine=True)) == [
        ["First T1"],
        ["T2"],
        ["Second T1"],
    ]


def test_manual_operation_joins_previous_toolpath_group():
    operations = [
        FakeSourceOperation("Rough", 1),
        FakeSourceOperation("Manual"),
        FakeSourceOperation("Finish", 2),
    ]

    assert names(group(operations)) == [
        ["Rough", "Manual"],
        ["Finish"],
    ]


def test_leading_manual_operations_join_first_toolpath_group():
    operations = [
        FakeSourceOperation("Manual 1"),
        FakeSourceOperation("Manual 2"),
        FakeSourceOperation("Rough", 1),
        FakeSourceOperation("Finish", 2),
    ]

    assert names(group(operations)) == [
        ["Manual 1", "Manual 2", "Rough"],
        ["Finish"],
    ]


def test_suppressed_operations_are_skipped_and_indices_are_preserved():
    operations = [
        FakeSourceOperation("Suppressed", 1, isSuppressed=True),
        FakeSourceOperation("Rough", 1),
        FakeSourceOperation("Also suppressed", isSuppressed=True),
        FakeSourceOperation("Finish", 2),
    ]
    groups = group(operations)

    assert names(groups) == [["Rough"], ["Finish"]]
    assert indices(groups) == [[1], [3]]


def test_all_suppressed_operations_produce_no_groups():
    operations = [
        FakeSourceOperation("One", 1, isSuppressed=True),
        FakeSourceOperation("Two", 2, isSuppressed=True),
    ]

    assert group(operations) == []
