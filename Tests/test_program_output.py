from pathlib import Path

import pytest

from addin_import import import_addin_module


program_output = import_addin_module("commands.postProcessor.program_output")
Constants = import_addin_module(
    "commands.postProcessor.settings.constants"
).Constants
ProgramOutputSettings = program_output.ProgramOutputSettings
plan_program_output = program_output.plan_program_output
prepare_output_folder = program_output.prepare_output_folder


class FakeOutputContext:
    def __init__(self, file_name):
        self.fileName = file_name
        self.events = []

    def set_file_name(self, file_name):
        self.fileName = file_name
        self.events.append(("set", file_name))


def settings(grouping, **overrides):
    values = {
        "operationsGrouping": grouping,
        "flatFileStructure": False,
        "numericName": False,
        "clearFolder": False,
    }
    values.update(overrides)
    return ProgramOutputSettings(**values)


def test_single_file_uses_output_folder_directly():
    output = Path("output")

    layout = plan_program_output(
        output,
        "job",
        settings(Constants.OperationsGroupings.SINGLE_FILE),
    )

    assert layout.path == output
    assert layout.fileName == "job"


@pytest.mark.parametrize(
    "grouping",
    [
        Constants.OperationsGroupings.SETUP,
        Constants.OperationsGroupings.SETUP_AND_TOOL,
        Constants.OperationsGroupings.PER_OPERATION,
    ],
)
def test_split_output_uses_program_subfolder(grouping):
    layout = plan_program_output(Path("output"), "job", settings(grouping))

    assert layout.path == Path("output/job")


def test_flat_structure_keeps_split_output_in_base_folder():
    layout = plan_program_output(
        Path("output"),
        "job",
        settings(
            Constants.OperationsGroupings.PER_OPERATION,
            flatFileStructure=True,
        ),
    )

    assert layout.path == Path("output")


def test_numeric_file_name_keeps_split_output_in_base_folder():
    layout = plan_program_output(
        Path("output"),
        "009",
        settings(
            Constants.OperationsGroupings.PER_OPERATION,
            numericName=True,
        ),
    )

    assert layout.path == Path("output")
    assert layout.fileName == "009"


def test_non_numeric_name_does_not_trigger_numeric_layout():
    layout = plan_program_output(
        Path("output"),
        "job",
        settings(
            Constants.OperationsGroupings.PER_OPERATION,
            numericName=True,
        ),
    )

    assert layout.path == Path("output/job")


def test_existing_file_is_not_a_valid_output_folder(tmp_path):
    output = tmp_path / "output"
    output.write_text("not a directory", encoding="utf-8")

    with pytest.raises(NotADirectoryError, match="not a directory"):
        prepare_output_folder(output, clearFolder=False)
    assert output.read_text(encoding="utf-8") == "not a directory"


def test_missing_output_folder_needs_no_preparation(tmp_path):
    output = tmp_path / "missing"

    prepare_output_folder(output, clearFolder=True)
    assert not output.exists()


def test_existing_output_is_preserved_when_clear_is_disabled(tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    file = output / "existing.nc"
    file.write_text("G1 X10", encoding="utf-8")

    prepare_output_folder(output, clearFolder=False)
    assert file.exists()


def test_clear_removes_files_directories_and_symlinks(tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    (output / "existing.nc").write_text("G1 X10", encoding="utf-8")
    nested = output / "nested"
    nested.mkdir()
    (nested / "nested.nc").write_text("M30", encoding="utf-8")
    target = tmp_path / "target.nc"
    target.write_text("keep", encoding="utf-8")
    (output / "linked.nc").symlink_to(target)

    prepare_output_folder(output, clearFolder=True)
    assert list(output.iterdir()) == []
    assert target.read_text(encoding="utf-8") == "keep"


def test_clear_reports_file_removal_failure(tmp_path, monkeypatch):
    output = tmp_path / "output"
    output.mkdir()
    protected = output / "protected.nc"
    protected.write_text("G1 X10", encoding="utf-8")
    original_unlink = Path.unlink

    def unlink(path, *args, **kwargs):
        if path == protected:
            raise PermissionError("protected")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", unlink)

    with pytest.raises(PermissionError, match="protected"):
        prepare_output_folder(output, clearFolder=True)
    assert protected.exists()
