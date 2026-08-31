import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Optional, overload

if TYPE_CHECKING:
    from adsk.core import Attributes as adskAttributes
else:
    adskAttributes = Any

from .. import config
from ..const import *
from ....config import PLUGIN_VERSION as GLOBAL_PLUGIN_VERSION

from .constants import Constants

_UNSET = object()

class _SettingsMeta(type):
    # Just to help Pylance to understand the code.
    _items: ClassVar[dict[str, Any]]

    # Just to help Pylance to understand the code.
    if TYPE_CHECKING:
        def get(cls, key: str) -> Any: ...
        def set(cls, key: str, value: Any) -> None: ...
    
    def __iter__(cls):
        return iter(cls._items)

    if TYPE_CHECKING:
        @overload
        def __call__(cls, key: str, /) -> Any: ...
        @overload
        def __call__(cls, key: str, value: Any, /) -> Any: ...

    def __call__(cls, key, /, value = _UNSET):
        if value is _UNSET:
            return cls.get(key)
        cls.set(key, value)
        return cls.get(key)

class Settings(Constants, metaclass=_SettingsMeta):
    """Manages the user settings for the Post Processor Add-In."""

    _session_only_settings = frozenset({
        Constants.OVERWRITE_FILES,
        Constants.CLEAR_FOLDER,
    })

    _default = None
    _path = None
    _must_save = False
    _inputs = None
    _items: dict[str, Any] = {}

    #region Initial default values of settings
    # See constants.py for details
    _default_settings = {
        Constants.END_CODES:                    "M5\nM9\nM30",
        Constants.OVERWRITE_FILES:              False,
        Constants.CLEAR_FOLDER:                 False,
        Constants.OUTPUT_FOLDER:                "",
        Constants.FILE_SEQUENCE:                False,
        Constants.NUMERIC_NAME:                 False,  
        Constants.FILE_SEQUENCE_DIGITS:         1,
        Constants.OPERATIONS_GROUPING:          Constants.OperationsGroupings.SETUP,
        Constants.COMBINE_TOOL:                 False,
        Constants.VERSION:                      config.SETTINGS_VERSION,
        Constants.PLUGIN_VERSION:               GLOBAL_PLUGIN_VERSION,
        Constants.NC_PROGRAM:                   "",
        Constants.LANGUAGE:                     "en",
        Constants.TOOL_CHANGE:                  "M9",
        Constants.RESTORE_RAPID_MOVES:          False,
        Constants.RAPID_MOVES_MINIMUM_DISTANCE: 20,
        Constants.RAPID_MOVES_MAX_STEPS:        3,
        Constants.INITIAL_DELAY:                0.2,
        Constants.POST_RETRIES:                 3,
        Constants.ROTATE_A_AXIS:                False,
        Constants.SAFE_Y_RETRACTION:            True,
        Constants.Y_RETRACTION_COORDINATE:      -100,
        Constants.FLAT_FILE_STRUCTURE:          False,
        Constants.USE_REGEX:                    False,
        Constants.FIND_STRING:                  "",
        Constants.REPLACE_STRING:               "",
        Constants.REPLACE_ONLY_SELECTED:        True,
        Constants.HEADER_END_CODES:             "G20\nG21",
    }
    #endregion

    @classmethod
    def load(cls, attr: Optional[adskAttributes] = None):
        if attr and attr.count > 0:
            try:
                cls._items = json.loads(attr.itemByName(Const.ATTR_GROUP, Const.ATTR_NAME).value)
                if cls._items.get(Constants.VERSION) is not None and cls._items[Constants.VERSION] == config.SETTINGS_VERSION:
                    cls._reset_session_only_settings()
                    return  # settings are valid for this version
            except Exception:
                pass
            
        # Document does not have valid settings, get defaults
        if not cls._default:
            # Haven't read the settings file yet
            file = None
            path = cls._settings_path()
            if path.exists() and path.is_file():
                with path.open() as file:
                    cls._default = json.load(file)
                cls.update(Settings._default_settings, cls._default)
            else:
                cls._default = dict(Settings._default_settings)
                cls._must_save = True
        
        if not cls._items:
            cls._items = dict(cls._default)
        else:
            cls.update(cls._default, cls._items)

        cls._reset_session_only_settings()

    @classmethod
    def save_default(cls):
        cls._must_save = False
        persistentItems = cls._persistent_items()
        cls._default = dict(persistentItems)
        try:
            strSettings = json.dumps(persistentItems, indent=4, sort_keys=True)
            with cls._settings_path().open("w") as file:
                file.write(strSettings)
        except Exception:
            pass

    @classmethod
    def save(cls, attr: adskAttributes):
        if cls._must_save:
            cls.save_default()
        cls.save_document(attr)

    @classmethod
    def save_document(cls, attr: adskAttributes) -> None:
        """Persist current settings to a Fusion document only."""
        attr.add(Const.ATTR_GROUP, Const.ATTR_NAME, json.dumps(cls._persistent_items()))

    @classmethod
    def _persistent_items(cls) -> dict[str, Any]:
        return {
            key: value
            for key, value in cls._items.items()
            if key not in cls._session_only_settings
        }

    @classmethod
    def _reset_session_only_settings(cls) -> None:
        for key in cls._session_only_settings:
            cls._items[key] = False
            
    @classmethod
    def update(cls, src, dst):
        for item in src:
            if not (item in dst):
                dst[item] = src[item]
        dst[Constants.VERSION] = src[Constants.VERSION]

    @classmethod
    def _settings_path(cls) -> Path:
        if not cls._path:
            pos = __file__.rfind(".")
            if pos == -1:
                pos = len(__file__)
            cls._path = __file__[0:pos] + Const.SETTINGS_FILE_EXT
        return Path(cls._path)
    
    @classmethod
    def get(cls, key) -> Any:
        return cls._items.get(key, None)
    
    @classmethod
    def set(cls, key: str, value: Any):
        cls._items[key] = value
        cls._must_save = True
