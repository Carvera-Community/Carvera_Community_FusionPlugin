from io import TextIOBase
from pathlib import Path
from typing import Optional, TextIO, Tuple, Union, overload

from ....lib.fusionAddInUtils.general_utils import Utils

from ..settings.settings import Settings
from .setup.setup import Setup

class SetupsBody():

    @classmethod
    def WriteBody(cls, path: Path, lineNumber: int, fileName: Optional[str] = None, fileExtension: Optional[str] = None) -> int:

        firstSetup: Optional[Setup] = None
        rotationAngle: float = 0
        currentRotationAngle: float = None
        preserveRotation: bool = False

        for setup in cls.selected:
            currentRotationAngle, rotationAngle, preserveRotation = cls._getRotation(setup, firstSetup, currentRotationAngle)
            if firstSetup is None:
                firstSetup = setup
            lineNumber = setup.WriteBody(path, lineNumber, fileName, fileExtension, rotationAngle = rotationAngle, preserveRotation = preserveRotation)
        return lineNumber

    def _getRotation(setup, firstSetup, currentRotation) -> Tuple[float, bool]:
        if Settings(Settings.ROTATE_A_AXIS): # Calculate the rotation between the setups
            angle = 0 if firstSetup is None else setup.GetRotationAroundXAxisRelativeToDeg(firstSetup)
            newRotation = None if angle == currentRotation else angle
            currentRotation = angle
            preserveRotation = firstSetup is None # Always use the rotation code of the first setup.
        else:
            preserveRotation = True # We don't want to do any changes to the native rotation code
        return currentRotation, newRotation, preserveRotation
