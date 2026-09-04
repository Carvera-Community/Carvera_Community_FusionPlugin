from pathlib import Path
from types import SimpleNamespace

import pytest

from addin_import import import_addin_module


program_module = import_addin_module("commands.postProcessor.program")
Parameters = import_addin_module("commands.postProcessor.parameters").Parameters
Program = program_module.Program


class FakeCollection:
    def __init__(self, values=None):
        self.values = {
            name: SimpleNamespace(name=name, value=value)
            for name, value in (values or {}).items()
        }

    def itemByName(self, name, attribute_name=None):
        key = name if attribute_name is None else (name, attribute_name)
        return self.values.get(key)

    def add(self, group, name, value):
        self.values[(group, name)] = SimpleNamespace(value=value)

    @property
    def count(self):
        return len(self.values)


class FakeValueAdapter:
    def get(self, parameter, value_type):
        return parameter.value

    def set(self, parameter, value):
        parameter.value = value


class FakeFusionAdapter:
    def __init__(self, atc=False, slots=1, a_axis=False, post_result=True):
        self.atc = atc
        self.slots = slots
        self.a_axis = a_axis
        self.post_result = post_result
        self.post_calls = []

    def machine_has_atc(self, program):
        return self.atc

    def machine_tool_slots(self, program):
        return self.slots

    def machine_has_a_axis(self, program):
        return self.a_axis

    def post_process(self, program):
        self.post_calls.append(list(program.operations))
        return self.post_result


def make_program(fusion_adapter=None, machine=None, post_configuration=None):
    parameters = FakeCollection(
        {
            Parameters.FILE_NAME: "job",
            Parameters.OUTPUT_FOLDER: "/tmp/output",
            Parameters.NAME: "Program",
            Parameters.OPEN_IN_EDITOR: True,
        }
    )
    source = SimpleNamespace(
        name="NC Program",
        hasError=False,
        isSelected=True,
        operations=[],
        isSuppressed=False,
        hasWarning=False,
        warning="",
        machine=machine,
        postConfiguration=post_configuration,
        attributes=FakeCollection(),
        parameters=parameters,
    )
    adapter = fusion_adapter or FakeFusionAdapter()
    return Program(source, adapter, FakeValueAdapter()), source, adapter


def test_program_exposes_source_state_and_parameters():
    program, source, _ = make_program()

    assert program.name == "NC Program"
    assert not program.has_error
    assert program.is_selected
    assert program.is_empty
    assert not program.is_suppressed
    assert not program.has_warning
    assert program.file_name == "job"

    program.set_file_name("updated")
    program.disable_open_in_editor()

    assert program.file_name == "updated"
    assert not program.parameters.get(Parameters.OPEN_IN_EDITOR, bool)


def test_machine_capabilities_are_delegated_to_fusion_adapter():
    adapter = FakeFusionAdapter(atc=True, slots=6, a_axis=True)
    program, _, _ = make_program(adapter, machine=SimpleNamespace(model="Makera"))

    assert program.has_machine
    assert program.machine_name == "Makera"
    assert program.machine_has_atc
    assert program.machine_tool_slots == 6
    assert program.machine_has_a_axis


def test_missing_machine_and_post_configuration_have_fallbacks():
    program, _, _ = make_program()

    assert not program.has_machine
    assert "no machine" in program.machine_name
    assert not program.has_post_processor
    assert "no post processor" in program.post_processor_description
    assert program.file_extension is None


def test_post_configuration_metadata_is_exposed():
    configuration = SimpleNamespace(description="Makera post", extension=".nc")
    program, _, _ = make_program(post_configuration=configuration)

    assert program.has_post_processor
    assert program.post_processor_description == "Makera post"
    assert program.file_extension == ".nc"


def test_post_process_rejects_empty_operation_list():
    program, _, adapter = make_program()

    assert not program.post_process([])
    assert adapter.post_calls == []


def test_post_process_assigns_operations_and_delegates():
    program, source, adapter = make_program()
    operations = [object(), object()]

    assert program.post_process(operations)
    assert source.operations == operations
    assert adapter.post_calls == [operations]


def test_output_folder_round_trips_through_parameters():
    program, _, _ = make_program()

    program.set_output_folder(Path("/tmp/new-output"))

    assert program.get_output_folder() == Path("/tmp/new-output")


def test_process_restores_program_parameters_after_parser_failure():
    program, _, _ = make_program()

    class FailingContext:
        def capture_processing_settings(self):
            return None

        def parse(self, _path):
            program.set_output_folder(Path("/tmp/temporary"))
            program.set_file_name("temporary")
            program.parameters.set(Parameters.NAME, "Temporary")
            raise RuntimeError("parse failed")

    with pytest.raises(RuntimeError, match="parse failed"):
        program.process(FailingContext(), Path("/tmp/work"))

    assert program.get_output_folder() == Path("/tmp/output")
    assert program.file_name == "job"
    assert program.parameters.get(Parameters.NAME, str) == "Program"


def test_write_output_restores_parameters_after_renderer_failure(monkeypatch):
    configuration = SimpleNamespace(description="Makera post", extension=".nc")
    program, _, _ = make_program(post_configuration=configuration)

    def fail_render(*_args):
        program.set_output_folder(Path("/tmp/temporary"))
        program.set_file_name("temporary")
        program.parameters.set(Parameters.NAME, "Temporary")
        raise RuntimeError("render failed")

    monkeypatch.setattr(program_module, "render_program_output", fail_render)

    with pytest.raises(RuntimeError, match="render failed"):
        program.write_output(object())

    assert program.get_output_folder() == Path("/tmp/output")
    assert program.file_name == "job"
    assert program.parameters.get(Parameters.NAME, str) == "Program"
