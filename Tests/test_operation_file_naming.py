import pytest

from addin_import import import_addin_module


naming = import_addin_module(
    "commands.postProcessor.operations.operation_file_naming"
)
Constants = import_addin_module(
    "commands.postProcessor.settings.constants"
).Constants
OperationFileNamingSettings = naming.OperationFileNamingSettings
get_operation_file_name = naming.get_operation_file_name


class FakeOperation:
    def __init__(self, index: int, name: str, tool_id: int | None):
        self.index = index
        self.name = name
        self.toolId = tool_id


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
    operation = FakeOperation(2, "Pocket", 7)

    file_name, next_name = get_operation_file_name(
        "setup", operation, 1, naming_settings(grouping), sanitize
    )

    assert file_name == "setup"
    assert next_name == "setup"


def test_setup_and_tool_names_first_tool_group():
    operation = FakeOperation(0, "Pocket", 7)

    file_name, _ = get_operation_file_name(
        "setup",
        operation,
        1,
        naming_settings(Constants.OperationsGroupings.SETUP_AND_TOOL),
        sanitize,
    )

    assert file_name == "setup_T7"


def test_setup_and_tool_indexes_repeated_tool_groups_and_sequences_files():
    operation = FakeOperation(4, "Pocket", 7)

    file_name, _ = get_operation_file_name(
        "setup",
        operation,
        2,
        naming_settings(
            Constants.OperationsGroupings.SETUP_AND_TOOL,
            fileSequence=True,
        ),
        sanitize,
    )

    assert file_name == "setup_005_T7_2"


def test_per_operation_uses_sanitized_operation_name():
    operation = FakeOperation(1, "Pocket / Finish", 7)

    file_name, _ = get_operation_file_name(
        "setup",
        operation,
        1,
        naming_settings(Constants.OperationsGroupings.PER_OPERATION),
        sanitize,
    )

    assert file_name == "Pocket___Finish"


def test_per_operation_can_prefix_sequence_number():
    operation = FakeOperation(1, "Finish", 7)

    file_name, _ = get_operation_file_name(
        "setup",
        operation,
        1,
        naming_settings(
            Constants.OperationsGroupings.PER_OPERATION,
            fileSequence=True,
        ),
        sanitize,
    )

    assert file_name == "002_Finish"


def test_numeric_naming_assigns_current_name_and_advances_context():
    operation = FakeOperation(0, "Pocket", 7)

    file_name, next_name = get_operation_file_name(
        "009",
        operation,
        1,
        naming_settings(
            Constants.OperationsGroupings.PER_OPERATION,
            numericName=True,
        ),
        sanitize,
    )

    assert file_name == "009"
    assert next_name == "010"


def test_pure_naming_returns_the_file_and_next_numeric_base():
    operation = FakeOperation(4, "Pocket", 7)

    file_name, next_name = get_operation_file_name(
        "009",
        operation,
        1,
        naming_settings(
            Constants.OperationsGroupings.PER_OPERATION,
            numericName=True,
        ),
        sanitize,
    )

    assert file_name == "009"
    assert next_name == "010"
