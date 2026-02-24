from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Tuple

from ...lib.fusionAddInUtils.general_utils import Utils
from ...lib.fusionAddInUtils.general_utils import classproperty



class _StringsMeta(type):
    def __call__(cls, raw: str, /, **kwargs) -> str:
        return cls.get(raw, **kwargs)


class Strings(metaclass=_StringsMeta):
    """Simple static loader for local component translations.

    Usage:
      Strings.load_local()  # loads commands/postProcessor/resources/i18n/*.json
      Strings.set_language('sv')
      label = Strings('This is the raw string')
    """

    _current: Dict[str, str] = {}
    _meta: Dict[str, Any] = {}
    _lang: str = "PROG" if Utils.DEBUG else "en"

    @classmethod
    def _i18n_dir(cls) -> Path:
        return Path(__file__).parent / "resources" / "i18n"

    @classmethod
    def set_language(cls, lang: str):
        """Set language and lazy-load that language file (if not already loaded)."""
        cls._lang = lang
        cls._current = {}
        cls._meta = {}
        languageFile = cls._i18n_dir() / f"{lang}.json"
        if not languageFile.exists():
            if Utils.DEBUG:
                Utils.log(f"Strings: language file not found: {languageFile}")
            return
        try:
            buffer = json.loads(languageFile.read_text(encoding="utf-8"))
            cls._meta, cls._current = cls._extractTranslation(buffer)
        except Exception:
            pass

    @classmethod
    def get(cls, raw: str, /, **kwargs) -> str:
        translation = cls._current.get(raw)
        out = translation if translation is not None else raw
        if translation is None and Utils.DEBUG and cls._lang != "PROG":
            Utils.log(f"Strings: missing translation for '{{}}' in language '{{}}'".format(raw, cls._lang))
        return out.format(**kwargs) if kwargs else out

    @classmethod
    def _flatten(cls, node: Any, out: dict[str, Any]) -> None:
        if isinstance(node, dict):
            key: str
            for key, value in node.items():
                if key.upper() == '__META__':
                    continue
                if isinstance(value, dict):
                    cls._flatten(value, out)
                else:
                    out[key] = value

    @classproperty
    def fileVersion(cls) -> str | None:
        return cls._meta.get('fileVersion')
        

    @classmethod
    def _extractTranslation(cls, buffer: any) -> Tuple[Dict[str, str], Dict[str, str]]:
        meta = buffer['__meta__'] if buffer.get('__meta__') is not None else {}
        translations = {}
        cls._flatten(buffer, translations)
        return meta, translations

    _availableLanguages = None

    @classmethod
    def GetAvailableLanguages(cls) -> dict[str, str]:
        if cls._availableLanguages is not None:
            return cls._availableLanguages
        
        cls._availableLanguages = {}

        for jsonFile in cls._i18n_dir().rglob('*.json'):
            with jsonFile.open(encoding='utf-8') as fileHandle:
                try:
                    data = json.load(fileHandle)
                except Exception as e:
                    if Utils.DEBUG:
                        Utils.log(f"Unable to load translation: {jsonFile.absolute()}\nException: {e}")
                    continue

                meta = data.get('__meta__')
                if meta is not None:
                    metaVersion = meta.get('metaVersion')
                    if metaVersion == 1:
                        local = meta.get('languageLocal')
                        english = meta.get('languageEnglish')
                        if local is not None and english is not None:
                            text = f"{local} ({english})"
                        elif local is not None:
                            text = local
                        elif english is not None:
                            text = english
                        else:
                            text = jsonFile.stem
                        cls._availableLanguages[jsonFile.stem] = text
                else:
                    cls._availableLanguages[jsonFile.stem] = jsonFile.stem

        return cls._availableLanguages
    
    @classmethod
    def GetLanguageSetting(cls, text: str) -> str:
       return {v: k for k, v in cls._availableLanguages.items()}.get(text)
