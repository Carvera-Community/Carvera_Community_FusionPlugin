from pathlib import Path
from types import SimpleNamespace

from addin_import import import_addin_module


body_writer = import_addin_module("commands.postProcessor.operations.body_writer")


class FakeOperation:
    def __init__(self, tool_id: int, body: str, has_body: bool = True):
        self.toolId = tool_id
        self.body = body
        self.hasBody = has_body
        self.fileName = None
        self.ctx = SimpleNamespace(rotationAngle=None, preserveRotation=None)

    def WriteBody(self, output) -> None:
        output.write(self.body)


def context(tmp_path: Path, operations):
    return SimpleNamespace(
        operations=operations,
        path=tmp_path,
        fileExtension=".nc",
        rotationAngle=45.0,
        preserveRotation=True,
    )


def assign_shared_name(ctx, operation, tool_index):
    operation.fileName = "shared"


def assign_tool_name(ctx, operation, tool_index):
    operation.fileName = f"T{operation.toolId}_{tool_index}"


def test_write_body_appends_operations_to_assigned_output_file(tmp_path):
    operations = [FakeOperation(7, "FIRST\n"), FakeOperation(8, "SECOND\n")]
    ctx = context(tmp_path, operations)

    body_writer.writeBody(ctx, assign_shared_name)

    assert (tmp_path / "shared.nc").read_text() == "FIRST\nSECOND\n"


def test_write_body_applies_setup_rotation_only_to_first_body(tmp_path):
    operations = [
        FakeOperation(1, "NO BODY\n", has_body=False),
        FakeOperation(7, "FIRST\n"),
        FakeOperation(8, "SECOND\n"),
    ]
    ctx = context(tmp_path, operations)

    body_writer.writeBody(ctx, assign_shared_name)

    assert operations[0].ctx.rotationAngle is None
    assert operations[0].ctx.preserveRotation is None
    assert operations[1].ctx.rotationAngle == 45.0
    assert operations[1].ctx.preserveRotation is True
    assert operations[2].ctx.rotationAngle is None
    assert operations[2].ctx.preserveRotation is False


def test_write_body_tracks_repeated_tool_indices(tmp_path):
    operations = [FakeOperation(7, "FIRST\n"), FakeOperation(7, "SECOND\n")]
    ctx = context(tmp_path, operations)

    body_writer.writeBody(ctx, assign_tool_name)

    assert (tmp_path / "T7_1.nc").read_text() == "FIRST\n"
    assert (tmp_path / "T7_2.nc").read_text() == "SECOND\n"
