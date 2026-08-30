from pathlib import Path
from types import SimpleNamespace

import pytest

from addin_import import import_addin_module


planning = import_addin_module(
    "commands.postProcessor.setups.output_path_planning"
)
Constants = import_addin_module(
    "commands.postProcessor.settings.constants"
).Constants
SetupOutputPathSettings = planning.SetupOutputPathSettings
getSetupOutputPath = planning.getSetupOutputPath


def settings(grouping, **overrides):
    values = {
        "flatFileStructure": False,
        "numericName": False,
        "operationsGrouping": grouping,
        "fileSequence": False,
        "fileSequenceDigits": 3,
    }
    values.update(overrides)
    return SetupOutputPathSettings(**values)


def sanitize(name):
    return name.replace(" ", "_").replace("/", "_")


@pytest.mark.parametrize(
    "grouping",
    [
        Constants.OperationsGroupings.SINGLE_FILE,
        Constants.OperationsGroupings.SETUP,
    ],
)
def test_shared_groupings_use_base_path(grouping):
    base_path = Path("output")
    setup = SimpleNamespace(index=1, name="Second Setup")

    assert getSetupOutputPath(
        base_path, setup, settings(grouping), sanitize
    ) == base_path


@pytest.mark.parametrize(
    "override",
    [
        {"flatFileStructure": True},
        {"numericName": True},
    ],
)
def test_flat_or_numeric_split_output_uses_base_path(override):
    base_path = Path("output")
    setup = SimpleNamespace(index=1, name="Second Setup")

    assert getSetupOutputPath(
        base_path,
        setup,
        settings(Constants.OperationsGroupings.PER_OPERATION, **override),
        sanitize,
    ) == base_path


@pytest.mark.parametrize(
    "grouping",
    [
        Constants.OperationsGroupings.SETUP_AND_TOOL,
        Constants.OperationsGroupings.PER_OPERATION,
    ],
)
def test_hierarchical_split_output_uses_sanitized_setup_folder(grouping):
    base_path = Path("output")
    setup = SimpleNamespace(index=1, name="Second / Setup")

    assert getSetupOutputPath(
        base_path, setup, settings(grouping), sanitize
    ) == Path("output/Second___Setup")


def test_sequence_prefix_uses_original_setup_index():
    base_path = Path("output")
    setup = SimpleNamespace(index=4, name="Finish")

    assert getSetupOutputPath(
        base_path,
        setup,
        settings(
            Constants.OperationsGroupings.SETUP_AND_TOOL,
            fileSequence=True,
        ),
        sanitize,
    ) == Path("output/005_Finish")
