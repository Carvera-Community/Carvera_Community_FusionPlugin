from typing import Final

from . import config
from ...config import PLUGIN_VERSION as GLOBAL_PLUGIN_VERSION
from ...lib.fusionAddInUtils.general_utils import *
from .const import *
import json

class _SettingsMeta(type):
    def __iter__(cls):
        return iter(cls._items)
    
    def __call__(cls, key, /):
        return cls.Get(key)

class Settings(metaclass=_SettingsMeta):
    """Manages the user settings for the Post Processor Add-In."""

    #region ----- Setting Keys -----
    # G-codes that mark the ending sequence
    END_CODES:                  Final[str] = 'endCodes'
    # If the files should be deleted before post processing
    DEL_FILES:                  Final[str] = 'delFiles'
    # If the folder should be deleted before post processing
    DEL_FOLDER:                 Final[str] = 'delFolder'
    # The name of the output folder
    OUTPUT_FOLDER:              Final[str] = 'outputFolder'
    # If sequence numbers should be used in file names/folders/operation steps
    SEQUENCE:                   Final[str] = 'sequence'
    # How much each sequence should be incremented each time
    SEQUENCE_INCREMENT:         Final[str] = 'sequenceIncrement'
    # If the name should be numeric
    NUMERIC_NAME:               Final[str] = 'numericName'
    # Number of digits to use in sequence names
    NAME_DIGITS:                Final[str] = 'nameDigits'
    # The interval that the numbering should increment by
    NUMBERING_INTERVAL:         Final[str] = 'numberingInterval'
    # If setups should be split into separate files
    OPERATIONS_GROUPING:        Final[str] = 'operationsGrouping'
    # If operations with the same tool should be combined
    COMBINE_TOOL:               Final[str] = 'combineTool'
    # Settings file version
    VERSION:                    Final[str] = 'version'
    # Plugin version
    PLUGIN_VERSION:             Final[str] = 'pluginVersion'
    # Currently selected NC Program
    NC_PROGRAM:                 Final[str] = 'ncProgram'
    # Currently selected language
    LANGUAGE:                   Final[str] = 'language'
    # G-code to Precede Tool Change
    TOOL_CHANGE:                Final[str] = 'toolChange'
    # If fast Z moves should be used
    RESTORE_RAPID_MOVES:        Final[str] = 'restoreRapidMoves'
    # Initial delay for retrying post processing
    INITIAL_DELAY:              Final[str] = 'initialDelay'
    # Number of retries for post processing
    POST_RETRIES:               Final[str] = 'postRetries'
    # If A-axis should be rotated between setups
    ROTATE_A_AXIS:              Final[str] = 'rotateAAxis'
    # If Y-axis should be retracted while A-axis rotates
    SAFE_Y_RETRACTION:          Final[str] = 'safeYRetraction'
    # The Y-axis coordinate to retract to when A-axis rotates
    # Note that it is a negative value as 0 is at the top of the bed
    Y_RETRACTION_COORDINATE:    Final[str] = 'yRetractionCoordinate'
    # If the folder structure should be flattned into the filenames
    FLAT_FILE_STRUCTURE:        Final[str] = 'flatFileStructure'
    # Use regular expressions for renaming setups
    USE_REGEX:                  Final[str] = 'useRegex'
    # The string to be found when renaming setups
    FIND_STRING:                Final[str] = 'findString'
    # The string to replace the found string when renaming setups
    REPLACE_STRING:             Final[str] = 'replaceString'
    # G-codes that ends the header section
    HEADER_END_CODES:           Final[str] = 'headerEndCodes'
    #endregion

    class Sequences:
        FILE:           Final[int] = 0
        STEP:           Final[int] = 1
        FILE_AND_STEP:  Final[int] = 2
        NONE:           Final[int] = 3

    class OperationsGroupings:
        SINGLE_FILE:    Final[int] = 0
        SETUP:          Final[int] = 1
        SETUP_AND_TOOL: Final[int] = 2
        PER_OPERATION:  Final[int] = 3

    _default = None
    _path = None
    _fMustSave = False
    _inputs = None
    _items = {}

    # Initial default values of settings
    # See above definitions for details
    _defaultSettings = {
        END_CODES:                  "M5\nM9\nM30",
        DEL_FILES:                  False,
        DEL_FOLDER:                 False,
        OUTPUT_FOLDER:              "",
        SEQUENCE:                   Sequences.NONE,
        SEQUENCE_INCREMENT:         5,
        NUMERIC_NAME:               False,  
        NAME_DIGITS:                1,
        NUMBERING_INTERVAL:         5,
        OPERATIONS_GROUPING:        OperationsGroupings.SETUP,
        COMBINE_TOOL:               False,
        VERSION:                    config.SETTINGS_VERSION,
        PLUGIN_VERSION:             GLOBAL_PLUGIN_VERSION,
        NC_PROGRAM:                 "",
        LANGUAGE:                   "en",
        TOOL_CHANGE:                "M9",
        RESTORE_RAPID_MOVES:        False,
        INITIAL_DELAY:              0.2,
        POST_RETRIES:               3,
        ROTATE_A_AXIS:              False,
        SAFE_Y_RETRACTION:          True,
        Y_RETRACTION_COORDINATE:    -100,
        FLAT_FILE_STRUCTURE:        False,
        USE_REGEX:                  False,
        FIND_STRING:                "",
        REPLACE_STRING:             "",
        HEADER_END_CODES:           "G20\nG21",
    }

    @classmethod
    def Load(cls, attr: adsk.core.Attributes):
        if attr:
            try:
                cls._items = json.loads(attr.itemByName(Const.ATTR_GROUP, Const.ATTR_NAME).value)
                if cls._items[Settings.VERSION] == GLOBAL_PLUGIN_VERSION:
                    return  # settings are valid for this version
            except Exception:
                pass
            
        # Document does not have valid settings, get defaults
        if not cls._default:
            # Haven't read the settings file yet
            file = None
            try:
                file = open(cls._getPath())
                cls._default = json.load(file)
                # never allow delFiles or delFolder to default to True
                cls._default[Settings.DEL_FILES] = False
                cls._default[Settings.DEL_FOLDER] = False
                if cls._default[Settings.VERSION] != GLOBAL_PLUGIN_VERSION:
                    cls.Update(Settings._defaultSettings, cls._default)
            except Exception:
                cls._default = dict(Settings._defaultSettings)
                cls._fMustSave = True
            finally:
                if file:
                    file.close()
        
        if not cls._items:
            cls._items = dict(cls._default)
        else:
            cls.Update(cls._default, cls._items)

    @classmethod
    def SaveDefault(cls):
        cls._fMustSave = False
        cls._default = dict(cls._items)
        # never allow delFiles or delFolder to default to True
        cls._default[Settings.DEL_FILES] = False
        cls._default[Settings.DEL_FOLDER] = False
        try:
            strSettings = json.dumps(cls._items, indent=4, sort_keys=True)
            file = open(cls._getPath(), "w")
            file.write(strSettings)
            file.close()
        except Exception:
            pass

    @classmethod
    def Save(cls, docAttr: adsk.core.Attributes):
        if cls._fMustSave:
            cls.SaveDefault()
        docAttr.add(Const.ATTR_GROUP, Const.ATTR_NAME, json.dumps(cls._items))
            
    @classmethod
    def Update(cls, src, dst):
        for item in src:
            if not (item in dst):
                dst[item] = src[item]
        dst[Settings.VERSION] = src[Settings.VERSION]

    @classmethod
    def _getPath(cls):
        if not cls._path:
            pos = __file__.rfind(".")
            if pos == -1:
                pos = len(__file__)
            cls._path = __file__[0:pos] + Const.SETTINGS_FILE_EXT
        return cls._path
    
    @classmethod
    def Get(cls, key):
        return cls._items.get(key, None)
    
    @classmethod
    def Set(cls, key, value):
        cls._items[key] = value
        cls._fMustSave = True