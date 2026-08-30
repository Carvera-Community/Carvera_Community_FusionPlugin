import json
from pathlib import Path

import pytest

from addin_import import import_addin_module


Const = import_addin_module("commands.postProcessor.const").Const
Constants = import_addin_module("commands.postProcessor.settings.constants").Constants
Settings = import_addin_module("commands.postProcessor.settings.settings").Settings


class FakeAttribute:
    def __init__(self, value: str):
        self.value = value


class FakeAttributes:
    def __init__(self, settings: dict | None = None):
        self._items = {}
        if settings is not None:
            self.add(Const.ATTR_GROUP, Const.ATTR_NAME, json.dumps(settings))

    @property
    def count(self) -> int:
        return len(self._items)

    def itemByName(self, group: str, name: str):
        return self._items.get((group, name))

    def add(self, group: str, name: str, value: str):
        self._items[(group, name)] = FakeAttribute(value)


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path):
    Settings._items = {}
    Settings._default = None
    Settings._path = str(tmp_path / "settings.settings")
    Settings._fMustSave = False


def test_save_excludes_session_only_safety_settings():
    Settings._items = dict(Settings._defaultSettings)
    Settings.set(Constants.LANGUAGE, "sv")
    Settings.set(Constants.OVERWRITE_FILES, True)
    Settings.set(Constants.CLEAR_FOLDER, True)
    attributes = FakeAttributes()

    Settings.save(attributes)

    saved = json.loads(attributes.itemByName(Const.ATTR_GROUP, Const.ATTR_NAME).value)
    assert saved[Constants.LANGUAGE] == "sv"
    assert Constants.OVERWRITE_FILES not in saved
    assert Constants.CLEAR_FOLDER not in saved
    assert Settings.get(Constants.OVERWRITE_FILES)
    assert Settings.get(Constants.CLEAR_FOLDER)


def test_load_resets_legacy_persisted_safety_settings():
    persisted = dict(Settings._defaultSettings)
    persisted[Constants.OVERWRITE_FILES] = True
    persisted[Constants.CLEAR_FOLDER] = True

    Settings.load(FakeAttributes(persisted))

    assert not Settings.get(Constants.OVERWRITE_FILES)
    assert not Settings.get(Constants.CLEAR_FOLDER)


def test_save_default_excludes_session_only_settings():
    Settings._items = dict(Settings._defaultSettings)
    Settings.set(Constants.OVERWRITE_FILES, True)
    Settings.set(Constants.CLEAR_FOLDER, True)

    Settings.save_default()

    saved = json.loads(Path(Settings._path).read_text(encoding="utf-8"))
    assert Constants.OVERWRITE_FILES not in saved
    assert Constants.CLEAR_FOLDER not in saved
