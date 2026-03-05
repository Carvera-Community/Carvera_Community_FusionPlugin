from typing import Optional

from ...settings.settings import Settings
from .setup_context import SetupContext

def writeHeaderStart(ctx: SetupContext) -> None:
    if ctx.operations is None:
        raise ValueError("ctx.operations is None")

    ctx.operations.WriteFirstHeaderStart()

def writeToolComments(ctx) -> None:
    if ctx.operations is None:
        raise ValueError("_operations is None")

    ctx.operations.WriteToolComments()

def writeHeaderEnd(ctx) -> None:
    if ctx.operations is None:
        raise ValueError("_operations is None")

    ctx.operations.WriteFirstHeaderEnd()

    # Bump up the file name for the next setup if numeric naming 
    # is enabled and we're not in SINGLE_FILE mode 
    # (which doesn't increment file names)
    if (Settings(Settings.NUMERIC_NAME) 
        and Settings(Settings.OPERATIONS_GROUPING) in [Settings.OperationsGroupings.SETUP]):
            if ctx.operations.fileName is None:
                raise ValueError("_operations.fileName is None")
            ctx.operations.SetFileName(str(int(ctx.operations.fileName) + 1).rjust(Settings(Settings.FILE_SEQUENCE_DIGITS), '0'))

def writeHeader(ctx) -> None:

    if ctx.operations is None:
        raise ValueError("ctx.operations is None")

    if Settings(Settings.FILE_SEQUENCE):
        fileNumber = str((ctx.index + 1)).rjust(Settings(Settings.FILE_SEQUENCE_DIGITS), '0')
        ctx.operations.SetFileName(f"{fileNumber}_{ctx.name}")
    else:
        ctx.operations.SetFileName(ctx.name)

    # SETUP writes one setup per file
    if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SETUP:
        writeHeaderStart(ctx)
        writeToolComments(ctx)
        writeHeaderEnd(ctx)
    else: # SETUP_AND_TOOL and PER_OPERATION breaks the setup down further
        if ctx.operations is None:
            raise ValueError("ctx.operations is None")
        ctx.operations.WriteHeader()
