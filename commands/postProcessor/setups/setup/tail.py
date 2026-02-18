from ...settings.settings import Settings

class SetupTail:
    @property
    def hasTail(self):
        return self._operations is not None and self._operations.hasTail
    
    def WriteTail(self):
        if self.hasTail:
            # SETUP writes the tail from the first operation.
            if Settings(Settings.OPERATIONS_GROUPING) in [Settings.OperationsGroupings.SINGLE_FILE,
                                                          Settings.OperationsGroupings.SETUP]:
                self._operations.SetLineNumber(self._lineNumber)
                self._operations.WriteFirstTail()
            else: # SETUP_AND_TOOL, PER_OPERATION
                self._operations.SetLineNumber(self._lineNumber)
                self._operations.WriteTail()
