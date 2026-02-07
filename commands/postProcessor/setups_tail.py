import io
from pathlib import Path
from typing import Optional, TextIO, Union, overload

from ...lib.fusionAddInUtils.general_utils import Utils

from .settings import Settings

class SetupsTail():
    #region GenerateTail code
    @overload
    @classmethod
    def WriteTail(cls, fileHandler: TextIO, lineNumber: int): ...

    @overload
    @classmethod
    def WriteTail(cls, folderPath: Path, lineNumber: int, fileName: Optional[str] = None, fileExtension: Optional[str] = None): ...

    # Runtime implementation of Generate
    @classmethod
    def WriteTail(cls, pathOrFile: Union[Path, TextIO], lineNumber: int, fileName: Optional[str] = None, fileExtension: Optional[str] = None):

        fileHandlerParam: Optional[TextIO] = None
        fileHandler: Optional[TextIO] = None

        if isinstance(pathOrFile, io.TextIOBase):
            fileHandlerParam: TextIO = pathOrFile
            fileHandler: TextIO = fileHandlerParam
        elif isinstance(pathOrFile, Path):
            pathParam: Path = pathOrFile
        else:
            raise TypeError("First argument must be either a file handler or a folder path.")
        
        try:
            # One tail for the whole program.
            if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SINGLE_FILE:
                setup = next((setup for setup in cls.selected if setup.hasTail and not setup.isSuppressed), None)
                if setup is None:
                    return lineNumber

                lineNumber = setup.WriteTail(fileHandler, lineNumber)
            
            else: # One tail per setup
                for setup in cls.selected:
                    if fileHandlerParam is None: # Create local file handler
                        fileHandler = cls._getFileHandler(cls.FileModes.APPEND, pathParam, fileName, setup, fileExtension)

                    lineNumber = setup.WriteTail(fileHandler, lineNumber)

            return lineNumber
        finally:
            if fileHandlerParam is None and fileHandler is not None: # local filehandler was opened, so close it
                fileHandler.close()
    #endregion
