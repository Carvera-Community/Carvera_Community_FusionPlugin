from ...settings.settings import Settings
from .setup_context import SetupContext

def writeBody(ctx: SetupContext):
    if ctx.operations is None:
        raise ValueError("ctx.operations is None")
    ctx.operations.WriteBody(ctx.rotationAngle, ctx.preserveRotation)

    # Bump up the file name for the next setup if numeric naming 
    # is enabled and we're in SETUP mode
    if (Settings(Settings.NUMERIC_NAME) 
        and Settings(Settings.OPERATIONS_GROUPING) in [Settings.OperationsGroupings.SETUP]):
            if ctx.operations.fileName is None:
                    raise ValueError("ctx.operations.fileName is None")
            ctx.operations.SetFileName(str(int(ctx.operations.fileName) + 1).rjust(Settings(Settings.FILE_SEQUENCE_DIGITS), '0'))

