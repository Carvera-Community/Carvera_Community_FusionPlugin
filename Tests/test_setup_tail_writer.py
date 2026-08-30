from types import SimpleNamespace

import pytest

from addin_import import import_addin_module


tail_writer = import_addin_module(
    "commands.postProcessor.setups.setup.tail_writer"
)
Constants = import_addin_module(
    "commands.postProcessor.settings.constants"
).Constants
SetupTailWriterSettings = tail_writer.SetupTailWriterSettings


class FakeOperations:
    def __init__(self, has_tail=True):
        self.hasTail = has_tail
        self.calls = []

    def WriteFirstTail(self) -> None:
        self.calls.append("first")

    def WriteTail(self) -> None:
        self.calls.append("split")


def settings(grouping):
    return SetupTailWriterSettings(operationsGrouping=grouping)


@pytest.mark.parametrize(
    "grouping",
    [
        Constants.OperationsGroupings.SINGLE_FILE,
        Constants.OperationsGroupings.SETUP,
    ],
)
def test_shared_groupings_write_first_detected_tail(grouping):
    operations = FakeOperations()

    tail_writer.writeTail(
        SimpleNamespace(operations=operations), settings(grouping)
    )

    assert operations.calls == ["first"]


@pytest.mark.parametrize(
    "grouping",
    [
        Constants.OperationsGroupings.SETUP_AND_TOOL,
        Constants.OperationsGroupings.PER_OPERATION,
    ],
)
def test_split_groupings_write_tail_to_each_result(grouping):
    operations = FakeOperations()

    tail_writer.writeTail(
        SimpleNamespace(operations=operations), settings(grouping)
    )

    assert operations.calls == ["split"]


def test_missing_operations_do_not_write_tail():
    tail_writer.writeTail(
        SimpleNamespace(operations=None),
        settings(Constants.OperationsGroupings.SETUP),
    )


def test_operations_without_detected_tail_do_not_write():
    operations = FakeOperations(has_tail=False)

    tail_writer.writeTail(
        SimpleNamespace(operations=operations),
        settings(Constants.OperationsGroupings.SETUP),
    )

    assert operations.calls == []
