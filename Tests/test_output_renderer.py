from pathlib import Path
from types import SimpleNamespace

import pytest

from addin_import import import_addin_module


renderer = import_addin_module("commands.postProcessor.output_renderer")
plan_module = import_addin_module("commands.postProcessor.output_plan")
PlannedBody = plan_module.PlannedBody
ResultFilePlan = plan_module.ResultFilePlan


class FakeOperation:
    def __init__(self, name):
        self.name = name
        self.ctx = SimpleNamespace()

    def write_header_start(self, output):
        output.write(f"HEADER {self.name}\n")

    def write_tool_comment(self, output):
        output.write(f"TOOL {self.name}\n")

    def write_header_end(self, output):
        output.write("HEADER END\n")

    def write_body(self, output):
        output.write(
            f"BODY {self.name} rotation={self.ctx.rotationAngle} "
            f"final={self.ctx.isLastOp}\n"
        )

    def write_tail(self, output):
        output.write(f"TAIL {self.name}\n")


def test_renderer_writes_one_complete_file_from_the_plan(tmp_path):
    first = FakeOperation("first")
    second = FakeOperation("second")
    path = tmp_path / "nested" / "job.nc"
    plan = ResultFilePlan(
        (0,),
        (),
        (first, second),
        path,
        first,
        (first, second),
        (
            PlannedBody(first, None, True, False),
            PlannedBody(second, 45, False, True),
        ),
        first,
    )

    written = renderer.render_output_files((plan,), overwrite_files=False)

    assert written == (path,)
    assert path.read_text() == (
        "HEADER first\n"
        "TOOL first\n"
        "TOOL second\n"
        "HEADER END\n"
        "BODY first rotation=None final=False\n"
        "BODY second rotation=45 final=True\n"
        "TAIL first\n"
    )


def test_renderer_refuses_to_overwrite_before_writing(tmp_path):
    path = tmp_path / "job.nc"
    path.write_text("existing")
    plan = ResultFilePlan((0,), (), (), path=path)

    with pytest.raises(FileExistsError):
        renderer.render_output_files((plan,), overwrite_files=False)

    assert path.read_text() == "existing"
