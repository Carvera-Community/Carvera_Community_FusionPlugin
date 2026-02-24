from ...settings.settings import Settings

class SetupBody:

    def WriteBody(self, rotationAngle: float, preserveRotation: bool) -> int:
        self._operations.SetLineNumber(self._lineNumber)
        self._operations.WriteBody(rotationAngle, preserveRotation)
        self._lineNumber = self._operations.lineNumber
    
        # Bump up the file name for the next setup if numeric naming 
        # is enabled and we're in SETUP mode
        if Settings(Settings.NUMERIC_NAME) \
            and Settings(Settings.OPERATIONS_GROUPING) in [Settings.OperationsGroupings.SETUP]:
                self._operations.SetFileName(str(int(self._operations.fileName) + 1).rjust(Settings(Settings.FILE_SEQUENCE_DIGITS), '0'))

