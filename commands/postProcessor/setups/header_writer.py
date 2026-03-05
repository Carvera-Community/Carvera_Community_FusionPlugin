from ..settings.settings import Settings

from .setups_context import SetupsContext

def writeHeader(ctx: SetupsContext):
    # SINGLE_FILE
    if Settings(Settings.OPERATIONS_GROUPING) in [Settings.OperationsGroupings.SINGLE_FILE]:
        firstSetup = next((setup for setup in ctx.selected if setup.hasOperationWithHeader), None)
        if firstSetup is not None: 
            firstSetup.WriteHeaderStart()
            for setup in ctx.selected:
                setup.WriteToolComments()
            firstSetup.WriteHeaderEnd()
    else: # SETUP / SETUP_AND_TOOL / PER_OPERATION
        fileName = None
        for setup in ctx.selected:
            if Settings(Settings.NUMERIC_NAME) and fileName is not None:
                setup.ctx.SetFileName(fileName)
            # SETUP starts at 0 each loop, the others continue incrementing from previous setup
            setup.WriteHeader()
            if Settings(Settings.NUMERIC_NAME) and setup.ctx.operations is not None:
                fileName = setup.ctx.operations.fileName
