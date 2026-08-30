from types import SimpleNamespace

import pytest

from addin_import import import_addin_module


header_writer = import_addin_module("commands.postProcessor.setups.header_writer")
Constants = import_addin_module(
    "commands.postProcessor.settings.constants"
).Constants
SetupsHeaderWriterSettings = header_writer.SetupsHeaderWriterSettings


class FakeSetupContext:
    def __init__(self, file_name=None, has_operations=True):
        self.operations = (
            SimpleNamespace(fileName=file_name) if has_operations else None
        )
        self.assigned_file_names = []

    def SetFileName(self, file_name):
        self.assigned_file_names.append(file_name)
        if self.operations is not None:
            self.operations.fileName = file_name


class FakeSetup:
    def __init__(
        self,
        name,
        *,
        has_header=False,
        output_file_name=None,
        has_operations=True,
    ):
        self.name = name
        self.hasOperationWithHeader = has_header
        self.output_file_name = output_file_name
        self.ctx = FakeSetupContext(has_operations=has_operations)
        self.calls = []

    def WriteHeaderStart(self):
        self.calls.append("start")

    def WriteToolComments(self):
        self.calls.append("tools")

    def WriteHeaderEnd(self):
        self.calls.append("end")

    def WriteHeader(self):
        self.calls.append("header")
        if self.ctx.operations is not None and self.output_file_name is not None:
            self.ctx.operations.fileName = self.output_file_name


def settings(grouping, numeric=False):
    return SetupsHeaderWriterSettings(
        operationsGrouping=grouping,
        numericName=numeric,
    )


def test_single_file_uses_first_setup_with_header():
    first = FakeSetup("No header")
    second = FakeSetup("Has header", has_header=True)
    third = FakeSetup("Later header", has_header=True)
    context = SimpleNamespace(selected=[first, second, third])

    header_writer.writeHeader(
        context, settings(Constants.OperationsGroupings.SINGLE_FILE)
    )

    assert first.calls == ["tools"]
    assert second.calls == ["start", "tools", "end"]
    assert third.calls == ["tools"]


def test_single_file_without_detected_header_writes_nothing():
    setups = [FakeSetup("One"), FakeSetup("Two")]

    header_writer.writeHeader(
        SimpleNamespace(selected=setups),
        settings(Constants.OperationsGroupings.SINGLE_FILE),
    )

    assert [setup.calls for setup in setups] == [[], []]


@pytest.mark.parametrize(
    "grouping",
    [
        Constants.OperationsGroupings.SETUP,
        Constants.OperationsGroupings.SETUP_AND_TOOL,
        Constants.OperationsGroupings.PER_OPERATION,
    ],
)
def test_non_single_groupings_delegate_header_to_each_setup(grouping):
    setups = [FakeSetup("One"), FakeSetup("Two")]

    header_writer.writeHeader(
        SimpleNamespace(selected=setups), settings(grouping)
    )

    assert [setup.calls for setup in setups] == [["header"], ["header"]]


def test_numeric_file_name_flows_between_setups():
    first = FakeSetup("One", output_file_name="010")
    second = FakeSetup("Two", output_file_name="011")

    header_writer.writeHeader(
        SimpleNamespace(selected=[first, second]),
        settings(Constants.OperationsGroupings.PER_OPERATION, numeric=True),
    )

    assert first.ctx.assigned_file_names == []
    assert second.ctx.assigned_file_names == ["010"]
