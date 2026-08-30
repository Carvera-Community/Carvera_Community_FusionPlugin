from dataclasses import FrozenInstanceError

import pytest

from addin_import import import_addin_module


module = import_addin_module("commands.postProcessor.processing_settings")
ProcessingSettings = module.ProcessingSettings
Settings = import_addin_module("commands.postProcessor.settings.settings").Settings


def test_capture_returns_an_immutable_snapshot():
    Settings._items = dict(Settings._defaultSettings)
    Settings._items[Settings.NUMERIC_NAME] = True
    snapshot = ProcessingSettings.capture()

    Settings._items[Settings.NUMERIC_NAME] = False

    assert snapshot.numericName is True
    with pytest.raises(FrozenInstanceError):
        snapshot.numericName = False
