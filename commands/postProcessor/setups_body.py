import io
from pathlib import Path
from typing import Optional, TextIO, overload

from .settings import Settings
from .setup import Setup

class SetupsBody():
    @overload
    @classmethod
    def WriteBody(cls, fileHandler: TextIO, lineNumber: int, addLineNumbers: bool, digits: int) -> int: ...

    @overload
    @classmethod
    def WriteBody(cls, folderPath: Path, lineNumber: int, addLineNumbers: bool, digits: int, fileName: str, fileExtension: str) -> int: ...

    @classmethod
    def WriteBody(cls, pathOrFile, lineNumber: int, addLineNumbers: Optional[bool] = None, digits: Optional[int] = None, fileName: Optional[str] = None, fileExtension: Optional[str] = None) -> int:

        fileHandlerParam: Optional[TextIO] = None
        firstSetup: Optional[Setup] = None
        rotationAngle: float = 0
        currentRotationAngle: float = None
        preserveRotation: bool = False

        if isinstance(pathOrFile, io.TextIOBase) and fileName is None and fileExtension is None:
            fileHandlerParam: TextIO = pathOrFile
            fileHandler: TextIO = fileHandlerParam
        try:
            for setup in cls.selected:
                if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SINGLE_FILE:
                    if fileHandlerParam is None: fileHandler = cls._getFileHandler(cls.FileModes.APPEND, pathOrFile, fileName, setup.name, fileExtension)
                    lineNumber = setup.WriteSetupName(fileHandler, addLineNumbers, lineNumber, digits)

                if Settings(Settings.ROTATE_A_AXIS):
                    angle = 0 if firstSetup is None else setup.GetRotationAroundXAxisRelativeToDeg(firstSetup)
                    rotationAngle = None if angle == currentRotationAngle else angle
                    currentRotationAngle = angle
                    preserveRotation = firstSetup is None
                else:
                    preserveRotation = True # We don't want to do any changes to the native rotation code

                if fileHandlerParam is None: fileHandler = cls._getFileHandler(cls.FileModes.APPEND, pathOrFile, fileName, setup.name, fileExtension)
                lineNumber = setup.WriteBody(fileHandler, lineNumber, addLineNumbers, digits, setup != firstSetup, rotationAngle = rotationAngle, preserveRotation = preserveRotation)

                if firstSetup is None:
                    firstSetup = setup
            return lineNumber
        
        finally:
            if fileHandlerParam is None and fileHandler is not None: # local filehandler was opened, so close it
                fileHandler.close()

    #endregion
