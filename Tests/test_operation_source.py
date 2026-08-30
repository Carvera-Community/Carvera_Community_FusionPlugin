from types import SimpleNamespace

from addin_import import import_addin_module


module = import_addin_module("commands.postProcessor.operations.operation_source")
OperationSource = module.OperationSource
raw_operation = module.raw_operation


def test_snapshot_keeps_decision_data_separate_from_runtime_identity():
    raw = object()
    source = OperationSource(raw, "Pocket", False, True, object(), 7)

    assert source.name == "Pocket"
    assert source.toolNumber == 7
    assert raw_operation(source) is raw


def test_legacy_sources_remain_valid_runtime_identities():
    source = SimpleNamespace(name="Pocket")

    assert raw_operation(source) is source
