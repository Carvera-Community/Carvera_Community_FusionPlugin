from .....lib.fusionAddInUtils.general_utils import Utils

from ...settings.settings import Settings
from ...line import Line

class SetupHeader(Line):
    @property
    def hasHeader(self):
        return self._operations is not None and self._operations.hasHeader

    def WriteHeaderStart(self) -> None:
        if not Settings(Settings.NUMERIC_NAME):
            self._setFileName()
        self._operations.WriteFirstHeaderStart()
        self._lineNumber = self._operations.lineNumber
    
    def WriteToolComments(self) -> None:
        self._operations.SetLineNumber(self._lineNumber)
        self._operations.WriteToolComments()
        self._lineNumber = self._operations.lineNumber
    
    def WriteHeaderEnd(self) -> None:
        self._operations.SetLineNumber(self._lineNumber)
        self._operations.WriteFirstHeaderEnd()
        self._lineNumber = self._operations.lineNumber

        # Bump up the file name for the next setup if numeric naming 
        # is enabled and we're not in SINGLE_FILE mode 
        # (which doesn't increment file names)
        if Settings(Settings.NUMERIC_NAME) \
            and Settings(Settings.OPERATIONS_GROUPING) in [Settings.OperationsGroupings.SETUP]:
                self._operations.SetFileName(str(int(self._operations.fileName) + Settings(Settings.FILE_SEQUENCE_INTERVAL)).rjust(Settings(Settings.FILE_SEQUENCE_DIGITS), '0'))

    def WriteHeader(self) -> None:
        # SETUP writes one setup per file
        if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SETUP:
            self.WriteHeaderStart()
            self.WriteToolComments()
            self.WriteHeaderEnd()
        else:
            # SETUP_AND_TOOL and PER_OPERATION breaks the setup down further
            if not Settings(Settings.NUMERIC_NAME):
                self._setFileName()
            self._operations.SetLineNumber(self._lineNumber)
            self._operations.WriteHeader()

    def _setFileName(self):
        if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SETUP:
            fileName = Utils.sanitizeFilename(self.name)
            if Settings(Settings.FILE_SEQUENCE):
                fileName = f"{str(self._index + 1).rjust(Settings(Settings.FILE_SEQUENCE_DIGITS), '0')}_{fileName}"
            self._operations.SetFileName(fileName)
