from pathlib import Path
from types import SimpleNamespace

from addin_import import import_addin_module


workflow = import_addin_module("commands.postProcessor.program_workflow")
Constants = import_addin_module(
    "commands.postProcessor.settings.constants"
).Constants


def make_context():
    settings = SimpleNamespace(
        operationsGrouping=Constants.OperationsGroupings.SINGLE_FILE,
        flatFileStructure=False,
        numericName=False,
        clearFolder=False,
        overwriteFiles=True,
    )
    context = SimpleNamespace(
        processingSettings=settings,
        selected=[],
        fileName=None,
        events=[],
        sanitizeFilename=lambda name: name,
    )
    context.setFileExtension = lambda value: context.events.append(("extension", value))
    context.setPath = lambda value: context.events.append(("path", value))
    context.setFileName = lambda value: context.events.append(("name", value))
    return context


def test_render_program_output_prepares_plans_and_renders(tmp_path, monkeypatch):
    context = make_context()
    rendered = []
    monkeypatch.setattr(workflow, "prepareOutputFolder", lambda path, clear: True)
    monkeypatch.setattr(workflow, "plan_output_files", lambda *args: ("plan",))
    monkeypatch.setattr(
        workflow,
        "render_output_files",
        lambda plans, overwrite: rendered.append((plans, overwrite)),
    )

    result = workflow.render_program_output(context, tmp_path, "job", ".nc")

    assert result
    assert context.events == [
        ("extension", ".nc"),
        ("path", tmp_path),
        ("name", "job"),
    ]
    assert rendered == [(('plan',), True)]


def test_render_program_output_stops_when_folder_preparation_fails(
    tmp_path,
    monkeypatch,
):
    context = make_context()
    monkeypatch.setattr(workflow, "prepareOutputFolder", lambda path, clear: False)

    assert not workflow.render_program_output(context, tmp_path, "job", ".nc")
    assert context.events == []
