import traceback
from typing import Optional, cast
from adsk.core import Application
from adsk.core import LogLevels
from adsk.core import LogTypes

class Utils():
    """A class containing general utility functions.
    """

    _app = Application.get()
    _ui = _app.userInterface

    # Attempt to read DEBUG flag from parent config.
    try:
        from ... import config as pluginConfig
        DEBUG = pluginConfig.DEBUG
    except:
        DEBUG = False

    @staticmethod
    def log(message: str, level: int = LogLevels.InfoLogLevel, force_console: bool = False):
        """Utility function to easily handle logging in your app.

        Arguments:
        message -- The message to log.
        level -- The logging severity level.
        force_console -- Forces the message to be written to the Text Command window. 
        """    
        # Always print to console, only seen through IDE.
        print(message)  

        # Log all errors to Fusion log file.
        if level == LogLevels.ErrorLogLevel:
            Utils._app.log(message, cast(LogLevels, level), cast(LogTypes, LogTypes.FileLogType))

        # If config.DEBUG is True write all log messages to the console.
        if Utils.DEBUG or force_console:
            Utils._app.log(message, cast(LogLevels, level), cast(LogTypes, LogTypes.ConsoleLogType))

    @staticmethod
    def handleError(name: str, show_message_box: bool = False):
        """Utility function to simplify error handling.

        Arguments:
        name -- A name used to label the error.
        show_message_box -- Indicates if the error should be shown in the message box.
                            If False, it will only be shown in the Text Command window
                            and logged to the log file.                        
        """    

        Utils.log('===== Error =====\n', LogLevels.ErrorLogLevel)
        Utils.log(f'{name}\n{traceback.format_exc()}', LogLevels.ErrorLogLevel)

        # If desired you could show an error as a message box.
        if show_message_box:
            Utils._ui.messageBox(f'{name}\n{traceback.format_exc()}')

    @staticmethod
    def sanitizeVariableName(s: str, *, allow_unicode: bool = True, max_length: Optional[int] = None) -> str:
        import keyword
        import re
        import unicodedata

        """Return a valid Python identifier based on s."""
        # Normalize unicode
        form = "NFKC" if allow_unicode else "NFKD"
        s = unicodedata.normalize(form, s)
        if not allow_unicode:
            s = s.encode("ascii", "ignore").decode("ascii")

        # Replace whitespace with underscore
        s = re.sub(r"\s+", "_", s)

        # Replace any non-identifier char with underscore
        if allow_unicode:
            s = re.sub(r"[^\w]", "_", s, flags=re.U)
        else:
            s = re.sub(r"[^A-Za-z0-9_]", "_", s)

        # Collapse multiple underscores and strip edges
        s = re.sub(r"_+", "_", s).strip("_")

        # Ensure not empty, not starting with digit, not a keyword
        if not s:
            s = "_"
        if s[0].isdigit():
            s = "_" + s
        if keyword.iskeyword(s):
            s = s + "_"

        # Optional length limit (keeps rules)
        if max_length is not None:
            s = s[:max_length]
            if not s[0].isalpha() and s[0] != "_":
                s = "_" + s
            if keyword.iskeyword(s):
                s = s + "_"

        return s

    @staticmethod
    def sanitizeFilename(name: str,
                        replacement: str = "_",
                        allowUnicode: bool = True,
                        maxLength: Optional[int] = None,
                        preserveExtension: bool = True,
                        *, platformPolicy: Optional[str] = None) -> str:
        """Return a safe filename derived from `name`.

        platformPolicy:
          - None = autodetect (Windows vs POSIX)
          - "windows" = strict Windows rules
          - "posix" = POSIX rules (only '/' + NUL + control chars removed)
        """
        import re, unicodedata, os, sys, platform

        # choose policy
        pol = (platformPolicy or ("windows" if platform.system().lower().startswith("win") else "posix")).lower()

        # forbidden char classes per policy
        if pol == "windows":
            forbidden = r"[\x00-\x1f<>:\"/\\|?*]"
        else:  # posix
            forbidden = r"[\x00-\x1f/]"  # allow more characters on POSIX

        # Split extension if desired
        if preserveExtension:
            base, ext = os.path.splitext(name)
        else:
            base, ext = name, ""

        # Normalize unicode
        form = "NFKC" if allowUnicode else "NFKD"
        s = unicodedata.normalize(form, base)
        if not allowUnicode:
            s = s.encode("ascii", "ignore").decode("ascii")

        # remove forbidden chars
        s = re.sub(forbidden, replacement, s)

        # Replace whitespace with single replacement
        s = re.sub(r"\s+", replacement, s)

        # Collapse multiple replacements
        rep = re.escape(replacement)
        s = re.sub(rf"{rep}+", replacement, s)

        # Strip leading/trailing spaces/dots/replacements
        s = s.strip(" ."+replacement)

        # Avoid empty name
        if not s:
            s = "_"

        # Windows reserved names handled only in windows policy
        if pol == "windows":
            reserved = {
                "CON","PRN","AUX","NUL",
                *(f"COM{i}" for i in range(1, 10)),
                *(f"LPT{i}" for i in range(1, 10)),
            }
            if s.upper() in reserved:
                s = s + "_"

        # Limit total length if requested (counting extension)
        if maxLength is not None:
            ext_len = len(ext)
            allowed = maxLength - ext_len
            if allowed <= 0:
                s = s[:maxLength]
                ext = ""
            else:
                s = s[:allowed]

        # Sanitize extension as well (remove forbidden chars for chosen policy)
        if ext:
            ext = re.sub(forbidden, "", ext)
            if not ext.startswith("."):
                ext = "." + ext

        return s + ext
    
    @staticmethod
    def maxFilenameLength(path: str = ".") -> int:
        import os
        if os.name == "nt":
            import ctypes, ctypes.wintypes
            root = os.path.abspath(path)
            root = os.path.splitdrive(root)[0] + "\\"
            GetVolumeInformationW = ctypes.windll.kernel32.GetVolumeInformationW
            max_comp = ctypes.wintypes.DWORD(0)
            res = GetVolumeInformationW(root, None, 0, None, None, ctypes.byref(max_comp), None, 0)
            if not res:
                raise OSError("GetVolumeInformationW failed")
            return int(max_comp.value)
        else:
            try:
                return int(os.pathconf(path, "PC_NAME_MAX"))
            except (AttributeError, OSError):
                # fallback common value
                return 255

class classproperty:
    def __init__(self, f):
        self.f = f
        self.fset = None
        self.name = None
    def __get__(self, obj, cls=None):
        if cls is None:
            cls = type(obj)
        return self.f(cls)
    def setter(self, fset):
        self.fset = fset
        return self
    def __set_name__(self, owner, name):
        self.name = name

