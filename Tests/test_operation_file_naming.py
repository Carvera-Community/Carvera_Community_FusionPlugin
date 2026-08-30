from dataclasses import dataclass

import pytest

from addin_import import import_addin_module


naming = import_addin_module(
    "commands.postProcessor.operations.operation_file_naming"
)
Constants = import_addin_module(
    "commands.postProcessor.settings.constants"
).Constants
OperationFileNamingSettings = naming.OperationFileNamingSettings
setOperationFileName = naming.setOperationFileName


@dataclass
class FakeContext:
    fileName: str


class FakeOperation:
    def __init__(self, index: int, name: str, tool_id: int | None):
        self.index = index
        self.name = name
        self.toolId = tool_id
        self.fileName = None

    def SetFileName(self, file_name: str) -> None:
        self.fileName = file_name


def naming_settings(grouping, **overrides) -> OperationFileNamingSettings:
    values = {
        "operationsGrouping": grouping,
        "fileSequenceDigits": 3,
        "numericName": False,
        "fileSequence": False,
    }
    values.update(overrides)
    return OperationFileNamingSettings(**values)


def sanitize(name: str) -> str:
    return name.replace(" ", "_").replace("/", "_")


@pytest.mark.parametrize(
    "grouping",
    [
        Constants.OperationsGroupings.SINGLE_FILE,
        Constants.OperationsGroupings.SETUP,
    ],
)
def test_shared_file_groupings_keep_context_file_name(grouping):
    context = FakeContext("setup")
    operation = FakeOperation(2, "Pocket", 7)

    setOperationFileName(
        context, operation, 1, naming_settings(grouping), sanitize
    )

    assert operation.fileName == "setup"
    assert context.fileName == "setup"


def test_setup_and_tool_names_first_tool_group():
    context = FakeContext("setup")
    operation = FakeOperation(0, "Pocket", 7)

    setOperationFileName(
        context,
        operation,
        1,
        naming_settings(Constants.OperationsGroupings.SETUP_AND_TOOL),
        sanitize,
    )

    assert operation.fileName == "setup_T7"


def test_setup_and_tool_indexes_repeated_tool_groups_and_sequences_files():
    context = FakeContext("setup")
    operation = FakeOperation(4, "Pocket", 7)

    setOperationFileName(
        context,
        operation,
        2,
        naming_settings(
            Constants.OperationsGroupings.SETUP_AND_TOOL,
            fileSequence=True,
        ),
        sanitize,
    )

    assert operation.fileName == "setup_005_T7_2"


def test_per_operation_uses_sanitized_operation_name():
    context = FakeContext("setup")
    operation = FakeOperation(1, "Pocket / Finish", 7)

    setOperationFileName(
        context,
        operation,
        1,
        naming_settings(Constants.OperationsGroupings.PER_OPERATION),
        sanitize,
    )

    assert operation.fileName == "Pocket___Finish"


def test_per_operation_can_prefix_sequence_number():
    context = FakeContext("setup")
    operation = FakeOperation(1, "Finish", 7)

    setOperationFileName(
        context,
        operation,
        1,
        naming_settings(
            Constants.OperationsGroupings.PER_OPERATION,
            fileSequence=True,
        ),
        sanitize,
    )

    assert operation.fileName == "002_Finish"


def test_numeric_naming_assigns_current_name_and_advances_context():
    context = FakeContext("009")
    operation = FakeOperation(0, "Pocket", 7)

    setOperationFileName(
        context,
        operation,
        1,
        naming_settings(
            Constants.OperationsGroupings.PER_OPERATION,
            numericName=True,
        ),
        sanitize,
    )

    assert operation.fileName == "009"
    assert context.fileName == "010"
