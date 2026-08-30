from pathlib import Path
from types import SimpleNamespace

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

    def machineHasATC(self, program):
        return self.atc

    def machineToolSlots(self, program):
        return self.slots

    def machineHasAAxis(self, program):
        return self.a_axis

    def postProcess(self, program):
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
    assert not program.hasError
    assert program.isSelected
    assert program.isEmpty
    assert not program.isSuppressed
    assert not program.hasWarning
    assert program.fileName == "job"

    program.SetFileName("updated")
    program.DisableOpenInEditor()

    assert program.fileName == "updated"
    assert not program.Parameters.Get(Parameters.OPEN_IN_EDITOR, bool)


def test_machine_capabilities_are_delegated_to_fusion_adapter():
    adapter = FakeFusionAdapter(atc=True, slots=6, a_axis=True)
    program, _, _ = make_program(adapter, machine=SimpleNamespace(model="Makera"))

    assert program.hasMachine
    assert program.machineName == "Makera"
    assert program.machineHasATC
    assert program.machineToolSlots == 6
    assert program.machineHasAAxis


def test_missing_machine_and_post_configuration_have_fallbacks():
    program, _, _ = make_program()

    assert not program.hasMachine
    assert "no machine" in program.machineName
    assert not program.hasPostProcessor
    assert "no post processor" in program.postProcessorDescription
    assert program.fileExtension is None


def test_post_configuration_metadata_is_exposed():
    configuration = SimpleNamespace(description="Makera post", extension=".nc")
    program, _, _ = make_program(post_configuration=configuration)

    assert program.hasPostProcessor
    assert program.postProcessorDescription == "Makera post"
    assert program.fileExtension == ".nc"


def test_post_process_rejects_empty_operation_list():
    program, _, adapter = make_program()

    assert not program.PostProcess([])
    assert adapter.post_calls == []


def test_post_process_assigns_operations_and_delegates():
    program, source, adapter = make_program()
    operations = [object(), object()]

    assert program.PostProcess(operations)
    assert source.operations == operations
    assert adapter.post_calls == [operations]


def test_output_folder_round_trips_through_parameters():
    program, _, _ = make_program()

    program.SetOutputFolder(Path("/tmp/new-output"))

    assert program.GetOutputFolder() == Path("/tmp/new-output")
