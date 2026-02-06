import io
from pathlib import Path
from typing import Optional, TextIO, overload

from .settings import Settings

class SetupsTail():
    #region GenerateTail code
    @overload
    @classmethod
    def WriteTail(cls, fileHandler: TextIO, lineNumber: int, addLineNumbers: bool, digits: int): ...

    @overload
    @classmethod
    def WriteTail(cls, folderPath: Path, lineNumber: int, addLineNumbers: bool, digits: int, fileName: str, fileExtension: str): ...

    # Runtime implementation of Generate
    @classmethod
    def WriteTail(cls, pathOrFile, lineNumber: int, addLineNumbers: Optional[bool] = None, digits: Optional[int] = None, fileExtension: Optional[str] = None):

        fileHandlerParam: Optional[TextIO] = None
        fileHandler: Optional[TextIO] = None

        if isinstance(pathOrFile, io.TextIOBase):
            fileHandlerParam: TextIO = pathOrFile
            fileHandler: TextIO = fileHandlerParam
        
        try:
            # One tail for the whole program.
            if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SINGLE_FILE:
                setup = next((setup for setup in cls.selected if setup.hasTail and not setup.isSuppressed), None)
                if setup is None:
                    return lineNumber

                if fileHandlerParam is None: fileHandler = cls._getFileHandler(cls.FileModes.APPEND, pathOrFile, '', setup.name, fileExtension)
                lineNumber = setup.WriteTail(fileHandler, lineNumber, addLineNumbers, digits)

            # One tail per setup
            if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SETUP:
                for setup in cls.selected:
                    if fileHandlerParam is None: fileHandler = cls._getFileHandler(cls.FileModes.APPEND, pathOrFile, '', setup.name, fileExtension)
                    lineNumber = setup.WriteTail(fileHandler, lineNumber, addLineNumbers, digits)


            return lineNumber
        finally:
            if fileHandlerParam is None and fileHandler is not None: # local filehandler was opened, so close it
                fileHandler.close()
    #endregion
