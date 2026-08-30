from types import SimpleNamespace

import pytest

from addin_import import import_addin_module


tail_writer = import_addin_module("commands.postProcessor.setups.tail_writer")
Constants = import_addin_module(
    "commands.postProcessor.settings.constants"
).Constants
SetupsTailWriterSettings = tail_writer.SetupsTailWriterSettings


class FakeSetupContext:
    def __init__(self, has_tail=False, has_operations=True):
        self.hasTail = has_tail
        self.operations = (
            SimpleNamespace(fileName=None) if has_operations else None
        )
        self.assigned_file_names = []

    def SetFileName(self, file_name):
        self.assigned_file_names.append(file_name)
        if self.operations is not None:
            self.operations.fileName = file_name


class FakeSetup:
    def __init__(
        self,
        *,
        has_tail=False,
        output_file_name=None,
        has_operations=True,
    ):
        self.ctx = FakeSetupContext(has_tail, has_operations)
        self.output_file_name = output_file_name
        self.write_calls = 0

    def WriteTail(self):
        self.write_calls += 1
        if self.ctx.operations is not None and self.output_file_name is not None:
            self.ctx.operations.fileName = self.output_file_name


def settings(grouping, numeric=False):
    return SetupsTailWriterSettings(
        operationsGrouping=grouping,
        numericName=numeric,
    )


def test_single_file_uses_first_setup_with_tail():
    setups = [
        FakeSetup(),
        FakeSetup(has_tail=True),
        FakeSetup(has_tail=True),
    ]

    tail_writer.writeTail(
        SimpleNamespace(selected=setups),
        settings(Constants.OperationsGroupings.SINGLE_FILE),
    )

    assert [setup.write_calls for setup in setups] == [0, 1, 0]


def test_single_file_without_tail_writes_nothing():
    setups = [FakeSetup(), FakeSetup()]

    tail_writer.writeTail(
        SimpleNamespace(selected=setups),
        settings(Constants.OperationsGroupings.SINGLE_FILE),
    )

    assert [setup.write_calls for setup in setups] == [0, 0]


@pytest.mark.parametrize(
    "grouping",
    [
        Constants.OperationsGroupings.SETUP,
        Constants.OperationsGroupings.SETUP_AND_TOOL,
        Constants.OperationsGroupings.PER_OPERATION,
    ],
)
def test_non_single_groupings_delegate_tail_to_each_setup(grouping):
    setups = [FakeSetup(has_tail=True), FakeSetup(has_tail=False)]

    tail_writer.writeTail(
        SimpleNamespace(selected=setups), settings(grouping)
    )

    assert [setup.write_calls for setup in setups] == [1, 1]


def test_numeric_file_name_flows_between_setups():
    first = FakeSetup(has_tail=True, output_file_name="010")
    second = FakeSetup(has_tail=True, output_file_name="011")

    tail_writer.writeTail(
        SimpleNamespace(selected=[first, second]),
        settings(Constants.OperationsGroupings.PER_OPERATION, numeric=True),
    )

    assert first.ctx.assigned_file_names == []
    assert second.ctx.assigned_file_names == ["010"]
