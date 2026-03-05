from .setup_context import SetupContext

from ...settings.settings import Settings
  
def writeTail(ctx: SetupContext):
    if ctx.operations.hasTail if ctx.operations is not None else False:
        if ctx.operations is None:
            raise ValueError("ctx.operations is None")
        
        # SETUP writes the tail from the first operation.
        if Settings(Settings.OPERATIONS_GROUPING) in [Settings.OperationsGroupings.SINGLE_FILE,
                                                        Settings.OperationsGroupings.SETUP]:
            ctx.operations.WriteFirstTail()
        else: # SETUP_AND_TOOL, PER_OPERATION
            ctx.operations.WriteTail()
