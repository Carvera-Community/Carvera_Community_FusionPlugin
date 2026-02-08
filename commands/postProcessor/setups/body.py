import io
from pathlib import Path
from typing import Optional, TextIO, Union, overload

from ....lib.fusionAddInUtils.general_utils import Utils

from ..settings import Settings
from .setup import Setup

class SetupsBody():
    @overload
    @classmethod
    def WriteBody(cls, fileHandler: TextIO, lineNumber: int) -> int: ...

    @overload
    @classmethod
    def WriteBody(cls, folderPath: Path, lineNumber: int, fileName: Optional[str] = None, fileExtension: Optional[str] = None) -> int: ...
    @classmethod
    def WriteBody(cls, pathOrFile: Union[Path, TextIO], lineNumber: int, fileName: Optional[str] = None, fileExtension: Optional[str] = None) -> int:

        fileHandlerParam: Optional[TextIO] = None
        firstSetup: Optional[Setup] = None
        rotationAngle: float = 0
        currentRotationAngle: float = None
        preserveRotation: bool = False

        if isinstance(pathOrFile, io.TextIOBase):
            fileHandlerParam: TextIO = pathOrFile
            fileHandler: TextIO = fileHandlerParam
        elif isinstance(pathOrFile, Path):
            pathParam: Path = pathOrFile
        else:
            raise TypeError("First argument must be either a file handler or a folder path.")

        try:
            for setup in cls.selected:
                if Settings(Settings.ROTATE_A_AXIS): # Calculate the rotation between the setups
                    angle = 0 if firstSetup is None else setup.GetRotationAroundXAxisRelativeToDeg(firstSetup)
                    rotationAngle = None if angle == currentRotationAngle else angle
                    currentRotationAngle = angle
                    preserveRotation = firstSetup is None # Always use the rotation code of the first setup.
                else:
                    preserveRotation = True # We don't want to do any changes to the native rotation code

                if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SINGLE_FILE:
                    lineNumber = setup.WriteSetupName(fileHandler, lineNumber)
                else:
                    if fileHandlerParam is None: # Create local file handler
                        fileHandler = cls._getFileHandler(cls.FileModes.APPEND, pathParam, fileName, setup, fileExtension)

                lineNumber = setup.WriteBody(fileHandler, lineNumber, rotationAngle = rotationAngle, preserveRotation = preserveRotation)

                if firstSetup is None:
                    firstSetup = setup
            return lineNumber
        
        finally:
            if fileHandlerParam is None and fileHandler is not None: # local filehandler was opened, so close it
                fileHandler.close()

    #endregion
