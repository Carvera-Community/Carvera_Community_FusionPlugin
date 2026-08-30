from types import SimpleNamespace

import pytest

from addin_import import import_addin_module


body_writer = import_addin_module("commands.postProcessor.setups.body_writer")
Constants = import_addin_module(
    "commands.postProcessor.settings.constants"
).Constants
SetupsBodyWriterSettings = body_writer.SetupsBodyWriterSettings


class FakeOperations:
    def __init__(self, operations, file_name=None):
        self._operations = operations
        self.fileName = file_name

    def __iter__(self):
        return iter(self._operations)


class FakeSetupContext:
    def __init__(self, operations):
        self.operations = operations
        self.rotationAngle = None
        self.preserveRotation = False
        self.assigned_file_names = []

    def SetFileName(self, file_name):
        self.assigned_file_names.append(file_name)
        if self.operations is not None:
            self.operations.fileName = file_name


class FakeSetup:
    def __init__(self, operations, relative_angle=0, next_file_name=None):
        self.ctx = FakeSetupContext(operations)
        self.relative_angle = relative_angle
        self.next_file_name = next_file_name
        self.write_calls = 0

    def GetRotationAroundXAxisRelativeToDeg(self, other_setup):
        return self.relative_angle

    def WriteBody(self):
        self.write_calls += 1
        if self.next_file_name is not None and self.ctx.operations is not None:
            self.ctx.operations.fileName = self.next_file_name


def operation(has_body=True):
    return SimpleNamespace(
        hasBody=has_body,
        ctx=SimpleNamespace(isLastOp=False),
    )


def settings(grouping, numeric=False, rotate=False):
    return SetupsBodyWriterSettings(
        operationsGrouping=grouping,
        numericName=numeric,
        rotateAAxis=rotate,
    )


def run(grouping, setups, **setting_values):
    context = SimpleNamespace(selected=setups, fileName="009")
    body_writer.writeBody(context, settings(grouping, **setting_values))
    return context


def test_single_file_marks_only_final_body_operation():
    first = [operation(), operation()]
    second = [operation(False), operation()]

    run(
        Constants.OperationsGroupings.SINGLE_FILE,
        [FakeSetup(FakeOperations(first)), FakeSetup(FakeOperations(second))],
    )

    assert [item.ctx.isLastOp for item in first] == [False, False]
    assert [item.ctx.isLastOp for item in second] == [False, True]


def test_setup_grouping_marks_final_body_in_each_setup():
    first = [operation(), operation()]
    second = [operation(), operation(False)]

    run(
        Constants.OperationsGroupings.SETUP,
        [FakeSetup(FakeOperations(first)), FakeSetup(FakeOperations(second))],
    )

    assert [item.ctx.isLastOp for item in first] == [False, True]
    assert [item.ctx.isLastOp for item in second] == [True, False]


@pytest.mark.parametrize(
    "grouping",
    [
        Constants.OperationsGroupings.SETUP_AND_TOOL,
        Constants.OperationsGroupings.PER_OPERATION,
    ],
)
def test_split_groupings_mark_every_body_operation_final(grouping):
    operations = [operation(), operation(False), operation()]

    run(grouping, [FakeSetup(FakeOperations(operations))])

    assert [item.ctx.isLastOp for item in operations] == [True, False, True]


def test_rotation_is_emitted_only_when_relative_angle_changes():
    setups = [
        FakeSetup(FakeOperations([]), relative_angle=0),
        FakeSetup(FakeOperations([]), relative_angle=45),
        FakeSetup(FakeOperations([]), relative_angle=45),
    ]

    run(Constants.OperationsGroupings.SINGLE_FILE, setups, rotate=True)

    assert [setup.ctx.rotationAngle for setup in setups] == [None, 45, None]
    assert [setup.ctx.preserveRotation for setup in setups] == [True, False, True]


def test_numeric_names_flow_between_split_setups():
    first = FakeSetup(FakeOperations([]), next_file_name="010")
    second = FakeSetup(FakeOperations([]), next_file_name="011")

    run(
        Constants.OperationsGroupings.PER_OPERATION,
        [first, second],
        numeric=True,
    )

    assert first.ctx.assigned_file_names == ["009"]
    assert second.ctx.assigned_file_names == ["010"]


def test_numeric_split_setup_requires_operations_after_write():
    setup = FakeSetup(None)

    with pytest.raises(ValueError, match="setup.ctx.operations is None"):
        run(
            Constants.OperationsGroupings.PER_OPERATION,
            [setup],
            numeric=True,
        )
