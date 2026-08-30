from types import SimpleNamespace

from addin_import import import_addin_module


module = import_addin_module("commands.postProcessor.setups.setup_source")
SetupSource = module.SetupSource
rawSetup = module.rawSetup


def test_setup_snapshot_separates_metadata_from_runtime_identity():
    raw = object()
    source = SetupSource(raw, "Top", True, False, False, True, None, ())

    assert source.name == "Top"
    assert source.hasWarning
    assert rawSetup(source) is raw


def test_legacy_setup_source_is_its_own_runtime_identity():
    source = SimpleNamespace(name="Top")

    assert rawSetup(source) is source
