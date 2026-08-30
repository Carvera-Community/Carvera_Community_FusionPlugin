import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Optional, overload

from adsk.core import Attributes as adskAttributes

from .. import config
from ..const import *
from ....config import PLUGIN_VERSION as GLOBAL_PLUGIN_VERSION
from ....lib.fusionAddInUtils.general_utils import *

from .constants import Constants

_UNSET = object()

class _SettingsMeta(type):
    # Just to help Pylance to understand the code.
    _items: ClassVar[dict[str, Any]]

    # Just to help Pylance to understand the code.
    if TYPE_CHECKING:
        def Get(cls, key: str) -> Any: ...
        def Set(cls, key: str, value: Any) -> None: ...
    
    def __iter__(cls):
        return iter(cls._items)

    if TYPE_CHECKING:
        @overload
        def __call__(cls, key: str, /) -> Any: ...
        @overload
        def __call__(cls, key: str, value: Any, /) -> Any: ...

    def __call__(cls, key, /, value = _UNSET):
        if value is _UNSET:
            return cls.Get(key)
        cls.Set(key, value)
        return cls.Get(key)

class Settings(Constants, metaclass=_SettingsMeta):
    """Manages the user settings for the Post Processor Add-In."""

    _sessionOnlySettings = frozenset({
        Constants.OVERWRITE_FILES,
        Constants.CLEAR_FOLDER,
    })

    _default = None
    _path = None
    _fMustSave = False
    _inputs = None
    _items: dict[str, Any] = {}

    #region Initial default values of settings
    # See constants.py for details
    _defaultSettings = {
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
    def Load(cls, attr: Optional[adskAttributes] = None):
        if attr and attr.count > 0:
            try:
                cls._items = json.loads(attr.itemByName(Const.ATTR_GROUP, Const.ATTR_NAME).value)
                if cls._items.get(Constants.VERSION) is not None and cls._items[Constants.VERSION] == config.SETTINGS_VERSION:
                    cls._resetSessionOnlySettings()
                    return  # settings are valid for this version
            except Exception:
                pass
            
        # Document does not have valid settings, get defaults
        if not cls._default:
            # Haven't read the settings file yet
            file = None
            path = cls._getPath()
            if path.exists and path.is_file():
                    with open(path) as file:
                        cls._default = json.load(file)
                    if cls._default[Constants.VERSION] != config.SETTINGS_VERSION:
                        cls.Update(Settings._defaultSettings, cls._default)
            else:
                cls._default = dict(Settings._defaultSettings)
                cls._fMustSave = True
        
        if not cls._items:
            cls._items = dict(cls._default)
        else:
            cls.Update(cls._default, cls._items)

        cls._resetSessionOnlySettings()

    @classmethod
    def SaveDefault(cls):
        cls._fMustSave = False
        persistentItems = cls._getPersistentItems()
        cls._default = dict(persistentItems)
        try:
            strSettings = json.dumps(persistentItems, indent=4, sort_keys=True)
            file = open(cls._getPath(), "w")
            file.write(strSettings)
            file.close()
        except Exception:
            pass

    @classmethod
    def Save(cls, attr: adskAttributes):
        if cls._fMustSave:
            cls.SaveDefault()
        attr.add(Const.ATTR_GROUP, Const.ATTR_NAME, json.dumps(cls._getPersistentItems()))

    @classmethod
    def _getPersistentItems(cls) -> dict[str, Any]:
        return {
            key: value
            for key, value in cls._items.items()
            if key not in cls._sessionOnlySettings
        }

    @classmethod
    def _resetSessionOnlySettings(cls) -> None:
        for key in cls._sessionOnlySettings:
            cls._items[key] = False
            
    @classmethod
    def Update(cls, src, dst):
        for item in src:
            if not (item in dst):
                dst[item] = src[item]
        dst[Constants.VERSION] = src[Constants.VERSION]

    @classmethod
    def _getPath(cls) -> Path:
        if not cls._path:
            pos = __file__.rfind(".")
            if pos == -1:
                pos = len(__file__)
            cls._path = __file__[0:pos] + Const.SETTINGS_FILE_EXT
        return Path(cls._path)
    
    @classmethod
    def Get(cls, key) -> Any:
        return cls._items.get(key, None)
    
    @classmethod
    def Set(cls, key: str, value: Any):
        cls._items[key] = value
        cls._fMustSave = True
