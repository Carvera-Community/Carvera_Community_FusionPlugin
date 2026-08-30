from types import SimpleNamespace

import pytest

from addin_import import import_addin_module


body_writer = import_addin_module(
    "commands.postProcessor.setups.setup.body_writer"
)
Constants = import_addin_module(
    "commands.postProcessor.settings.constants"
).Constants
SetupBodyWriterSettings = body_writer.SetupBodyWriterSettings


class FakeOperations:
    def __init__(self, file_name="setup"):
        self.fileName = file_name
        self.body_calls = []

    def WriteBody(self, rotation_angle, preserve_rotation) -> None:
        self.body_calls.append((rotation_angle, preserve_rotation))

    def SetFileName(self, file_name: str) -> None:
        self.fileName = file_name


def settings(grouping, numeric=False, digits=3):
    return SetupBodyWriterSettings(
        numericName=numeric,
        operationsGrouping=grouping,
        fileSequenceDigits=digits,
    )


def test_write_body_forwards_setup_rotation():
    operations = FakeOperations()
    context = SimpleNamespace(
        operations=operations,
        rotationAngle=45.0,
        preserveRotation=False,
    )

    body_writer.writeBody(
        context, settings(Constants.OperationsGroupings.SINGLE_FILE)
    )

    assert operations.body_calls == [(45.0, False)]


def test_write_body_rejects_missing_operations():
    context = SimpleNamespace(
        operations=None,
        rotationAngle=None,
        preserveRotation=False,
    )

    with pytest.raises(ValueError, match="ctx.operations is None"):
        body_writer.writeBody(
            context, settings(Constants.OperationsGroupings.SETUP)
        )


def test_setup_grouping_advances_numeric_file_name():
    operations = FakeOperations("009")
    context = SimpleNamespace(
        operations=operations,
        rotationAngle=None,
        preserveRotation=True,
    )

    body_writer.writeBody(
        context,
        settings(Constants.OperationsGroupings.SETUP, numeric=True),
    )

    assert operations.fileName == "010"


def test_other_groupings_do_not_advance_numeric_file_name():
    operations = FakeOperations("009")
    context = SimpleNamespace(
        operations=operations,
        rotationAngle=None,
        preserveRotation=True,
    )

    body_writer.writeBody(
        context,
        settings(Constants.OperationsGroupings.PER_OPERATION, numeric=True),
    )

    assert operations.fileName == "009"


def test_numeric_setup_requires_an_assigned_file_name():
    operations = FakeOperations(None)
    context = SimpleNamespace(
        operations=operations,
        rotationAngle=None,
        preserveRotation=True,
    )

    with pytest.raises(ValueError, match="ctx.operations.fileName is None"):
        body_writer.writeBody(
            context,
            settings(Constants.OperationsGroupings.SETUP, numeric=True),
        )
