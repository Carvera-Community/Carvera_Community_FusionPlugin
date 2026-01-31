from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Optional

from ...lib.fusionAddInUtils.general_utils import Utils


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
    _lang: str = "PROG" if Utils.DEBUG else "en"

    @classmethod
    def _i18n_dir(cls) -> Path:
        return Path(__file__).parent / "resources" / "i18n"

    @classmethod
    def set_language(cls, lang: str):
        """Set language and lazy-load that language file (if not already loaded)."""
        cls._lang = lang
        p = cls._i18n_dir() / f"{lang}.json"
        if not p.exists():
            if getattr(Utils, 'DEBUG', False):
                Utils.log(f"Strings: language file not found: {p}")
            cls._current = {}
            return
        try:
            cls._current = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            cls._current = {}

    @classmethod
    def get(cls, raw: str, /, **kwargs) -> str:
        translation = cls._current.get(raw)
        out = translation if translation is not None else raw
        if translation is None and getattr(Utils, 'DEBUG', False) and cls._lang != "PROG":
            Utils.log(f"Strings: missing translation for '{{}}' in language '{{}}'".format(raw, cls._lang))
        return out.format(**kwargs) if kwargs else out
