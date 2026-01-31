from typing import Final
import adsk.cam

class Parameters:
    """The CAM parameters of the Fusion NCProgram."""
    def __init__(self, NCParameters: adsk.cam.NCParameters):
        self._parameters = NCParameters

    FILE_NAME: Final      = 'nc_program_filename'
    OPEN_IN_EDITOR: Final = 'nc_program_openInEditor'
    OUTPUT_FOLDER: Final  = 'nc_program_output_folder'
    NAME: Final           = 'nc_program_name'
    EXTENSION: Final      = 'nc_program_nc_extension'

    def Get(self, name: str):
        """Returns the value of the NCParameter with the given name, or None if it does not exist."""
        param = self._parameters.itemByName(name)
        # TODO: Do a type check here to check if there is a wrapper or not
        return param.value.value if param is not None and param.value is not None else None
    
    def Set(self, name: str, value):
        """Sets the value of the NCParameter with the given name."""
        param = self._parameters.itemByName(name)
        # TODO: Do a type check here to check if there is a wrapper or not
        if param is not None and param.value is not None:
            param.value.value = value