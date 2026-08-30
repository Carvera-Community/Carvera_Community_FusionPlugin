from pathlib import Path
from types import SimpleNamespace

import pytest

from addin_import import import_addin_module


temporary = import_addin_module(
    "commands.postProcessor.operations.operation.temporary_post_processing"
)
TemporaryPostProcessPolicy = temporary.TemporaryPostProcessPolicy
create_temporary_operation_file = temporary.create_temporary_operation_file


def test_post_processes_to_unique_temporary_path_and_parses_result(tmp_path):
    context = SimpleNamespace(name="Pocket", tempFilePath=Path())
    source_operations = [object(), object()]
    calls = []

    def post_process(operations, output_folder, file_name):
        calls.append((operations, output_folder, file_name))
        (output_folder / f"{file_name}.nc").write_text("G1 X10\n")
        return True

    parsed = []
    create_temporary_operation_file(
        context,
        tmp_path,
        source_operations,
        ".nc",
        post_process,
        parsed.append,
        createId=lambda: "operation-id",
    )

    assert context.tempFilePath == tmp_path / "operation-id.nc"
    assert calls == [(source_operations, tmp_path, "operation-id")]
    assert parsed == [context]


def test_none_extension_is_not_appended(tmp_path):
    context = SimpleNamespace(name="Manual", tempFilePath=Path())

    def post_process(operations, output_folder, file_name):
        (output_folder / file_name).touch()
        return True

    create_temporary_operation_file(
        context,
        tmp_path,
        [],
        None,
        post_process,
        lambda ctx: None,
        createId=lambda: "operation-id",
    )

    assert context.tempFilePath == tmp_path / "operation-id"


def test_failed_post_process_stops_before_waiting_or_parsing(tmp_path):
    context = SimpleNamespace(name="Pocket", tempFilePath=Path())
    sleeps = []
    parsed = []

    with pytest.raises(RuntimeError, match="Pocket post processing failed"):
        create_temporary_operation_file(
            context,
            tmp_path,
            [],
            ".nc",
            lambda operations, output_folder, file_name: False,
            parsed.append,
            createId=lambda: "operation-id",
            sleep=sleeps.append,
        )

    assert sleeps == []
    assert parsed == []


def test_waits_with_increasing_delay_until_output_exists(tmp_path):
    context = SimpleNamespace(name="Pocket", tempFilePath=Path())
    sleeps = []

    def sleep(delay):
        sleeps.append(delay)
        if len(sleeps) == 2:
            context.tempFilePath.touch()

    create_temporary_operation_file(
        context,
        tmp_path,
        [],
        ".nc",
        lambda operations, output_folder, file_name: True,
        lambda ctx: None,
        createId=lambda: "operation-id",
        sleep=sleep,
    )

    assert sleeps == [0.1, 0.2]


def test_missing_output_fails_after_configured_attempts(tmp_path):
    context = SimpleNamespace(name="Pocket", tempFilePath=Path())
    sleeps = []
    parsed = []

    with pytest.raises(RuntimeError, match="output file was not created"):
        create_temporary_operation_file(
            context,
            tmp_path,
            [],
            ".nc",
            lambda operations, output_folder, file_name: True,
            parsed.append,
            policy=TemporaryPostProcessPolicy(initialDelay=0.25, maxAttempts=3),
            createId=lambda: "operation-id",
            sleep=sleeps.append,
        )

    assert sleeps == [0.25, 0.5, 0.75]
    assert parsed == []
