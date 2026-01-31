#  Copyright 2022 by Autodesk, Inc.
#  Permission to use, copy, modify, and distribute this software in object code form
#  for any purpose and without fee is hereby granted, provided that the above copyright
#  notice appears in all copies and that both that copyright notice and the limited
#  warranty and restricted rights notice below appear in all supporting documentation.
#
#  AUTODESK PROVIDES THIS PROGRAM "AS IS" AND WITH ALL FAULTS. AUTODESK SPECIFICALLY
#  DISCLAIMS ANY IMPLIED WARRANTY OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR USE.
#  AUTODESK, INC. DOES NOT WARRANT THAT THE OPERATION OF THE PROGRAM WILL BE
#  UNINTERRUPTED OR ERROR FREE.

import traceback
import adsk.core

class Utils():
    """A class containing general utility functions.
    """

    _app = adsk.core.Application.get()
    _ui = _app.userInterface

    # Attempt to read DEBUG flag from parent config.
    try:
        from ... import config as pluginConfig
        DEBUG = pluginConfig.DEBUG
    except:
        DEBUG = False

    @staticmethod
    def log(message: str, level: adsk.core.LogLevels = adsk.core.LogLevels.InfoLogLevel, force_console: bool = False):
        """Utility function to easily handle logging in your app.

        Arguments:
        message -- The message to log.
        level -- The logging severity level.
        force_console -- Forces the message to be written to the Text Command window. 
        """    
        # Always print to console, only seen through IDE.
        print(message)  

        # Log all errors to Fusion log file.
        if level == adsk.core.LogLevels.ErrorLogLevel:
            log_type = adsk.core.LogTypes.FileLogType
            Utils._app.log(message, level, log_type)

        # If config.DEBUG is True write all log messages to the console.
        if Utils.DEBUG or force_console:
            log_type = adsk.core.LogTypes.ConsoleLogType
            Utils._app.log(message, level, log_type)

    @staticmethod
    def handle_error(name: str, show_message_box: bool = False):
        """Utility function to simplify error handling.

        Arguments:
        name -- A name used to label the error.
        show_message_box -- Indicates if the error should be shown in the message box.
                            If False, it will only be shown in the Text Command window
                            and logged to the log file.                        
        """    

        Utils.log('===== Error =====', adsk.core.LogLevels.ErrorLogLevel)
        Utils.log(f'{name}\n{traceback.format_exc()}', adsk.core.LogLevels.ErrorLogLevel)

        # If desired you could show an error as a message box.
        if show_message_box:
            Utils._ui.messageBox(f'{name}\n{traceback.format_exc()}')

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
