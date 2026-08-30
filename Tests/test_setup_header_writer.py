from types import SimpleNamespace

import pytest

from addin_import import import_addin_module


header_writer = import_addin_module(
    "commands.postProcessor.setups.setup.header_writer"
)
Constants = import_addin_module(
    "commands.postProcessor.settings.constants"
).Constants
SetupHeaderWriterSettings = header_writer.SetupHeaderWriterSettings


class FakeOperations:
    def __init__(self, file_name="initial"):
        self.fileName = file_name
        self.calls = []

    def SetFileName(self, file_name: str) -> None:
        self.fileName = file_name

    def WriteFirstHeaderStart(self) -> None:
        self.calls.append("start")

    def WriteToolComments(self) -> None:
        self.calls.append("tools")

    def WriteFirstHeaderEnd(self) -> None:
        self.calls.append("end")

    def WriteHeader(self) -> None:
        self.calls.append("split")


def settings(grouping, **overrides):
    values = {
        "numericName": False,
        "operationsGrouping": grouping,
        "fileSequence": False,
        "fileSequenceDigits": 3,
    }
    values.update(overrides)
    return SetupHeaderWriterSettings(**values)


def context(operations):
    return SimpleNamespace(operations=operations, index=1, name="Second Setup")


def test_setup_grouping_writes_shared_header_sections():
    operations = FakeOperations()

    header_writer.writeHeader(
        context(operations),
        settings(Constants.OperationsGroupings.SETUP),
    )

    assert operations.fileName == "Second Setup"
    assert operations.calls == ["start", "tools", "end"]


def test_split_grouping_delegates_to_operations_header():
    operations = FakeOperations()

    header_writer.writeHeader(
        context(operations),
        settings(Constants.OperationsGroupings.PER_OPERATION),
    )

    assert operations.fileName == "Second Setup"
    assert operations.calls == ["split"]


def test_file_sequence_prefixes_setup_name():
    operations = FakeOperations()

    header_writer.writeHeader(
        context(operations),
        settings(
            Constants.OperationsGroupings.SETUP,
            fileSequence=True,
        ),
    )

    assert operations.fileName == "002_Second Setup"


def test_numeric_setup_header_advances_file_name():
    operations = FakeOperations("009")
    ctx = context(operations)

    header_writer.writeHeaderEnd(
        ctx,
        settings(Constants.OperationsGroupings.SETUP, numericName=True),
    )

    assert operations.calls == ["end"]
    assert operations.fileName == "010"


def test_header_helpers_reject_missing_operations():
    ctx = context(None)

    with pytest.raises(ValueError):
        header_writer.writeHeaderStart(ctx)
    with pytest.raises(ValueError):
        header_writer.writeToolComments(ctx)
    with pytest.raises(ValueError):
        header_writer.writeHeaderEnd(
            ctx, settings(Constants.OperationsGroupings.SETUP)
        )
    with pytest.raises(ValueError):
        header_writer.writeHeader(
            ctx, settings(Constants.OperationsGroupings.SETUP)
        )


def test_numeric_setup_header_requires_file_name():
    operations = FakeOperations(None)

    with pytest.raises(ValueError, match="_operations.fileName is None"):
        header_writer.writeHeaderEnd(
            context(operations),
            settings(Constants.OperationsGroupings.SETUP, numericName=True),
        )
