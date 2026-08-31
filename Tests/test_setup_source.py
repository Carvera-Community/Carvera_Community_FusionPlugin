from types import SimpleNamespace

from addin_import import import_addin_module


module = import_addin_module("commands.postProcessor.setups.setup_source")
SetupSource = module.SetupSource
raw_setup = module.raw_setup


def test_setup_snapshot_separates_metadata_from_runtime_identity():
    raw = object()
    source = SetupSource(raw, "Top", True, False, False, True, None, ())

    assert source.name == "Top"
    assert source.hasWarning
    assert raw_setup(source) is raw


def test_legacy_setup_source_is_its_own_runtime_identity():
    source = SimpleNamespace(name="Top")

    assert raw_setup(source) is source
