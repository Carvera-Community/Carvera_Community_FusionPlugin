from ..settings.settings import Settings
from ..line import Line

class SetupsHeader(Line):

    @classmethod
    def WriteHeader(cls):
        # SINGLE_FILE
        if Settings(Settings.OPERATIONS_GROUPING) in [Settings.OperationsGroupings.SINGLE_FILE]:
            firstSetup = next((setup for setup in cls.selected if setup.hasHeader), None)
            if firstSetup is not None: 
                firstSetup.WriteHeaderStart()
                cls._lineNumber = firstSetup.lineNumber
                for setup in cls.selected:
                    setup.SetLineNumber(cls._lineNumber)
                    setup.WriteToolComments()
                    cls._lineNumber = setup.lineNumber
                firstSetup.SetLineNumber(cls._lineNumber)
                firstSetup.WriteHeaderEnd()
                cls._lineNumber = firstSetup.lineNumber
        else: # SETUP / SETUP_AND_TOOL / PER_OPERATION
            fileName = None
            for setup in cls.selected:
                if Settings(Settings.NUMERIC_NAME) and fileName is not None:
                    setup.SetFileName(fileName)
                # SETUP starts at 0 each loop, the others continue incrementing from previous setup
                if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SETUP:
                    setup.SetLineNumber(0)
                else:
                    setup.SetLineNumber(cls._lineNumber)
                setup.WriteHeader()
                if Settings(Settings.NUMERIC_NAME):
                    fileName = setup._operations.fileName
