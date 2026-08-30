import json

from addin_import import import_addin_module


strings_module = import_addin_module("commands.postProcessor.strings")
Strings = strings_module.Strings


def reset_strings():
    Strings._current = {}
    Strings._meta = {}
    Strings._availableLanguages = None
    Strings._lang = "en"


def test_flatten_ignores_metadata_and_flattens_sections():
    output = {}

    Strings._flatten(
        {
            "__meta__": {"fileVersion": "1"},
            "section": {"Hello": "Hej"},
            "Plain": "Value",
        },
        output,
    )

    assert output == {"Hello": "Hej", "Plain": "Value"}


def test_extract_translation_separates_metadata():
    meta, translations = Strings._extractTranslation(
        {"__meta__": {"fileVersion": "2"}, "Hello": "Hej"}
    )

    assert meta == {"fileVersion": "2"}
    assert translations == {"Hello": "Hej"}


def test_get_returns_translation_fallback_and_formatting():
    reset_strings()
    Strings._current = {"Hello {name}": "Hej {name}"}

    assert Strings("Hello {name}", name="Ada") == "Hej Ada"
    assert Strings("Missing") == "Missing"


def test_set_language_loads_translation_file(tmp_path, monkeypatch):
    reset_strings()
    translation = {
        "__meta__": {"fileVersion": "3"},
        "Hello": "Hej",
    }
    (tmp_path / "sv.json").write_text(json.dumps(translation), encoding="utf-8")
    monkeypatch.setattr(Strings, "_i18n_dir", classmethod(lambda cls: tmp_path))

    Strings.set_language("sv")

    assert Strings("Hello") == "Hej"
    assert Strings.fileVersion == "3"


def test_missing_language_resets_current_translation(tmp_path, monkeypatch):
    reset_strings()
    Strings._current = {"Old": "Gammal"}
    monkeypatch.setattr(Strings, "_i18n_dir", classmethod(lambda cls: tmp_path))

    Strings.set_language("missing")

    assert Strings._current == {}


def test_available_languages_uses_metadata_and_filename_fallback(tmp_path, monkeypatch):
    reset_strings()
    (tmp_path / "sv.json").write_text(
        json.dumps(
            {
                "__meta__": {
                    "metaVersion": 1,
                    "languageLocal": "Svenska",
                    "languageEnglish": "Swedish",
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "plain.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(Strings, "_i18n_dir", classmethod(lambda cls: tmp_path))

    languages = Strings.GetAvailableLanguages()

    assert languages == {"plain": "plain", "sv": "Svenska (Swedish)"}
    assert Strings.GetLanguageSetting("Svenska (Swedish)") == "sv"
