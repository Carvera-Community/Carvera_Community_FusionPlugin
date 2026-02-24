from ..settings.settings import Settings

class SetupsTail():
    @classmethod
    def WriteTail(cls):

        if Settings(Settings.OPERATIONS_GROUPING) in [Settings.OperationsGroupings.SINGLE_FILE]:
            firstSetup = next((setup for setup in cls.selected if setup.hasHeader), None)

            if firstSetup is not None:
                firstSetup.WriteTail()
        else: # SETUP, SETUP_AND_TOOL, PER_OPERATION
            fileName = None
            for setup in cls.selected:
                if Settings(Settings.NUMERIC_NAME) and fileName is not None:
                    setup.SetFileName(fileName)
                setup.WriteTail()
                if Settings(Settings.NUMERIC_NAME):
                    fileName = setup._operations.fileName
    