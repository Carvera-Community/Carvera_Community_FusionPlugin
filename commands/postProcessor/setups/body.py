from pathlib import Path
from typing import Optional, Tuple


from ..settings.settings import Settings
from .setup.setup import Setup

class SetupsBody():

    @classmethod
    def WriteBody(cls):

        fileName = None
        firstSetup: Optional[Setup] = None
        rotationAngle: float = 0
        currentRotationAngle: float = None
        preserveRotation: bool = False
        
        setup: Setup
        if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SINGLE_FILE:
            for setup in cls.selected:
                if firstSetup is not None:
                    setup.SetLineNumber(firstSetup.lineNumber) # Continue from the line number of the first setup
                currentRotationAngle, rotationAngle, preserveRotation = cls._getRotation(setup, firstSetup, currentRotationAngle)
                if firstSetup is None:
                    firstSetup = setup
                if Settings(Settings.NUMERIC_NAME) and fileName is not None:
                    setup.SetFileName(fileName)
                setup.WriteBody(rotationAngle, preserveRotation)
                firstSetup.SetLineNumber(setup.lineNumber) # Collect the new lineNumber
            return

        for setup in cls.selected:
            currentRotationAngle, rotationAngle, preserveRotation = cls._getRotation(setup, firstSetup, currentRotationAngle)
            if firstSetup is None:
                firstSetup = setup
            if Settings(Settings.NUMERIC_NAME) and fileName is not None:
                setup.SetFileName(fileName)
            setup.WriteBody(rotationAngle, preserveRotation)
            cls._lineNumber = setup.lineNumber
            if Settings(Settings.NUMERIC_NAME):
                fileName = setup._operations.fileName 

    def _getRotation(setup: Setup, firstSetup: Optional[Setup], currentRotation: Optional[float]) -> Tuple[float, Optional[float], bool]:
        if Settings(Settings.ROTATE_A_AXIS): # Calculate the rotation between the setups
            angle = 0 if firstSetup is None else setup.GetRotationAroundXAxisRelativeToDeg(firstSetup)
            newRotation = None if angle == currentRotation else angle
            currentRotation = angle
            preserveRotation = firstSetup is None # Always use the rotation code of the first setup.
        else:
            preserveRotation = True # We don't want to do any changes to the native rotation code
        return currentRotation, newRotation, preserveRotation
