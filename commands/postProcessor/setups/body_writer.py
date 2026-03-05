from typing import Optional, Tuple

from .setups_context import SetupsContext

from ..settings.settings import Settings
from .setup.setup import Setup

def writeBody(ctx: SetupsContext):
    
    firstSetup: Setup | None = None
    currentRotationAngle: float | None = None

    def _getRotation(setup: Setup, firstSetup: Optional[Setup], currentRotation: Optional[float]) -> Tuple[float | None, float | None, bool]:
        newRotation = None
        if Settings(Settings.ROTATE_A_AXIS): # Calculate the rotation between the setups
            angle = 0 if firstSetup is None else setup.GetRotationAroundXAxisRelativeToDeg(firstSetup)
            newRotation = None if angle == currentRotation else angle
            currentRotation = angle
            preserveRotation = firstSetup is None # Always use the rotation code of the first setup.
        else:
            preserveRotation = True # We don't want to do any changes to the native rotation code
        return currentRotation, newRotation, preserveRotation


    if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SINGLE_FILE:
        for setup in ctx.selected:
            currentRotationAngle, setup.ctx.rotationAngle, setup.ctx.preserveRotation = _getRotation(setup, firstSetup, currentRotationAngle)
            if firstSetup is None:
                firstSetup = setup
            if Settings(Settings.NUMERIC_NAME) and ctx.fileName is not None:
                setup.ctx.SetFileName(ctx.fileName)
            setup.WriteBody()
        return

    for setup in ctx.selected:
        currentRotationAngle, setup.ctx.rotationAngle, setup.ctx.preserveRotation = _getRotation(setup, firstSetup, currentRotationAngle)
        if firstSetup is None:
            firstSetup = setup
        if Settings(Settings.NUMERIC_NAME) and fileName is not None:
            setup.ctx.SetFileName(fileName)
        setup.WriteBody()
        if Settings(Settings.NUMERIC_NAME):
            if setup.ctx.operations is None:
                raise ValueError("setup._operations is None")
            fileName = setup.ctx.operations.fileName 

