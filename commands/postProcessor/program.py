from __future__ import annotations
import os
import adsk
import adsk.cam
from pathlib import Path


from .strings import Strings
from .attributes import Attributes
from .setups import Setups
from .settings import Settings
from .parameters import Parameters

def CountOutputFolderFiles(folder, limit, fileExt):
    cntFiles = 0
    cntNcFiles = 0
    for path, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith(fileExt):
                cntNcFiles += 1
            else:
                cntFiles += 1
        if cntFiles > limit:
            return "many files that are not G-code"
        if cntNcFiles > limit * 1.5:
            return "many more G-code files than are produced by this design"
    return None


class Program():
    def __init__(self, program: adsk.cam.NCProgram):
        self._program: adsk.cam.NCProgram = program
        self._outputFolder: Path = None
        self._attributes: Attributes = Attributes(program.attributes)
        self._parameters: Parameters = Parameters(program.parameters)

    @property
    def programName(self):
        """Returns the name of the NCProgram."""
        return self._program.name
    
    @property
    def hasError(self):
        """Returns whether the NCProgram has an error."""
        return self._program.hasError
    
    @property
    def isSelected(self):
        """Returns whether the NCProgram is selected."""
        return self._program.isSelected

    @property
    def isEmpty(self):
        """Returns whether the NCProgram is empty (has no operations)."""
        return len(self._program.operations) == 0
    
    @property
    def isSuppressed(self):
        """Returns whether the NCProgram is suppressed."""
        return self._program.isSuppressed
    
    @property
    def hasWarning(self):
        """Returns whether the NCProgram has a warning."""
        return self._program.hasWarning
    
    @property
    def warning(self):
        """Returns the warnings of the NCProgram."""
        return self._program.warning

    @property
    def Parameters(self):
        return self._parameters
    
    @property
    def attributes(self):
        return self._attributes
    
    @property
    def machineName(self):
        """Returns the machine of the NCProgram."""
        return self._program.machine.model if self._program.machine is not None else Strings("<no machine chosen>")

    @property
    def machineHasAAxis(self):
        """Returns whether the machine has A axis."""
        return self._program.machine.elements.defaultItemByType('controller').axisConfigurations.itemById('U') is not None \
            if self._program.machine is not None \
            else False
    
    @property
    def postProcessorDescription(self):
        """Returns the post processor of the current NCProgram."""
        return self._program.postConfiguration.description if self._program.postConfiguration else Strings("<no post processor chosen>")
    
    @property
    def fileName(self):
        """Returns the file name of the NCProgram."""
        return self.Parameters.Get(Parameters.FILE_NAME)

    def SetFileName(self, fileName: str):
        """Sets the file name of the NCProgram."""
        self.Parameters.Set(Parameters.FILE_NAME, fileName)

    @property
    def fileExtension(self):
        """Returns the file extension of the NCProgram."""
        return self._program.postConfiguration.extension if self._program.postConfiguration else None

    def Process(self, tmpPath: Path):
        """Generate the initial G-code files from the Fusion NCProgram using the Post Processor 
            and gather information for generation of final files."""
        oldOutputFolder = self.GetOutputFolder()

        #region --- Flyttas till Generate ---
        # if not Settings.Get(Settings.DEL_FILES):
        #     Settings.Set(Settings.DEL_FOLDER, False) # Only remove folders if files will be removed too

        # if Settings.Get(Settings.DEL_FOLDER):
        #     strMsg = CountOutputFolderFiles(self._outputFolder, Setups.Count(), self.fileExtension)
        #     if strMsg:
        #         Settings.Set(Settings.DEL_FOLDER, False)
        #         strMsg = (
        #             "The output folder contains {}. "
        #             "It will not be deleted. You may wish to make sure you selected "
        #             "the correct folder. If you want the folder deleted, you must "
        #             "do it manually."
        #             ).format(strMsg)
        #         res = self._ui.messageBox(strMsg, 
        #                             Const.CMD_NAME,
        #                             adsk.core.MessageBoxButtonTypes.OKCancelButtonType,
        #                             adsk.core.MessageBoxIconTypes.WarningIconType)
        #         if res == adsk.core.DialogResults.DialogCancel:
        #             return  # abort!

        # if Settings.Get(Settings.DEL_FOLDER):
        #     try:
        #         shutil.rmtree(self._outputFolder, True)
        #     except:
        #         pass #ignore errors

        # # Make sure that the root folder exists as defined in the NC Program parameters
        # self.SetAndCreateOutputFolder()

        # TODO: Start showing progress here
        #endregion

        outputFolder = self.GetOutputFolder()
        fileName = self.fileName
        name = self.Parameters.Get(Parameters.NAME)

        try:
            Setups.Parse(tmpPath)
        finally:
            self.SetOutputFolder(outputFolder)
            self.Parameters.Set(Parameters.FILE_NAME, fileName)
            self.Parameters.Set(Parameters.NAME, name)

        # Restore the output folder in the NC Program parameters
        self.SetOutputFolder(oldOutputFolder)

    def Generate(self):
        """Generate the final G-code files from the results of the post processing."""
        outputFolder = self.GetOutputFolder()
        fileName = self.fileName
        name = self.Parameters.Get(Parameters.NAME)
        addLineNumbers = Settings(Settings.SEQUENCE) in [Settings.Sequences.STEP, Settings.Sequences.FILE_AND_STEP]
        digits = Settings.Get(Settings.NAME_DIGITS)

        try:
            if not outputFolder.exists():
                outputFolder.mkdir(parents=True)

            fileName = self.fileName
            lineNumber = 0            
            fileExtension = self._program.postConfiguration.extension

            if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SINGLE_FILE:
                outputFolder.mkdir(parents=True, exist_ok=True)
                filePath = outputFolder / f"{fileName}{fileExtension}"
                with filePath.open("w", encoding="utf-8") as fileHandler:
                    lineNumber = Setups.WriteHeader(fileHandler, lineNumber, addLineNumbers, digits)
                    lineNumber = Setups.WriteBody(fileHandler, lineNumber, addLineNumbers, digits)
                    
                    if(Setups.hasOperationWithTail):
                        Setups.WriteTail(fileHandler, lineNumber, addLineNumbers, digits)
            else: # Output with folder structure
                if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SETUP:
                    if Settings(Settings.FLAT_FILE_STRUCTURE):
                        folder = outputFolder
                    else:
                        folder = outputFolder / self.fileName
                        folder.mkdir(parents=True, exist_ok=True)
                    Setups.WriteHeader(folder, lineNumber, addLineNumbers, digits, fileName, fileExtension)
                    Setups.WriteBody(folder, lineNumber, addLineNumbers, digits, fileName, fileExtension)
                    if(Setups.hasOperationWithTail):
                        Setups.WriteTail(folder, lineNumber, addLineNumbers, digits, fileName, fileExtension)

                elif Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.PER_OPERATION:
                    if Settings(Settings.FLAT_FILE_STRUCTURE):
                        folder = outputFolder
                    else:
                        folder = outputFolder / self.fileName
                        folder.mkdir(parents=True, exist_ok=True)
                    Setups.WriteOperations(folder, lineNumber, addLineNumbers, digits, fileName, fileExtension)

        except Exception as exc:
            raise exc
        finally:
            self.SetOutputFolder(outputFolder)
            self.Parameters.Set(Parameters.FILE_NAME, fileName)
            self.Parameters.Set(Parameters.NAME, name)

    def DisableOpenInEditor(self):
        """Convenience method for disabling "Open in Editor" option"""
        self.Parameters.Set(Parameters.OPEN_IN_EDITOR, False)

    def PostProcess(self, operations):
        if len(operations) == 0:
            return False # Nothing to process
        self._program.operations = operations
        return self._program.postProcess(adsk.cam.NCProgramPostProcessOptions.create())

    def SetOutputFolder(self, folder: Path):
        """Convenience method to set and verify output folder"""
        self.Parameters.Set(Parameters.OUTPUT_FOLDER, folder.as_posix())
        result = self.GetOutputFolder()
        if result != folder and folder[0:2] == "\\\\":
            self.Parameters.Set(Parameters.OUTPUT_FOLDER, "\\\\" + folder)    # double up leading "\"
        return None

    def GetOutputFolder(self) -> Path:
        """Convenience method to get output folder"""
        return Path(self.Parameters.Get(Parameters.OUTPUT_FOLDER))

    def SetAndCreateOutputFolder(self):
        """Sets and if needed creates the output folder as defined in the Fusion NCProgram parameters"""
        rawPath = self.GetOutputFolder()

        # Preserve UNC/network paths as-is; otherwise use pathlib with
        # expanded user and env vars. Use splitdrive to detect UNC (no ':' in
        # the drive part) rather than ad-hoc prefix checks.
        drive = os.path.splitdrive(rawPath)[0]
        is_unc = False
        if drive:
            is_unc = not drive.endswith(':')

        if is_unc: # Windows UNC path
            outputFolder = Path(rawPath)
        else: # Local Windows or Posix path, lets get an absolute path
            outputFolder = Path(os.path.expandvars(os.path.expanduser(rawPath))).resolve(strict=False)

        # Ensure directory exists — check existence as normal flow; only
        # handle mkdir failures as exceptional cases.
        if not outputFolder.exists(): 
            # let's collect exceptions higher up for now. 
            # A nicer error handling pattern would be nice, 
            # (like Promise or something) but let's focus 
            # on other things for now.
            outputFolder.mkdir(parents=True, exist_ok=True) 
        elif not outputFolder.is_dir():
            # Path exists but is not a directory
            raise Exception(f"Output folder '{outputFolder.as_posix()}' exists and is not a folder.")

        # Compute compact form (use ~ when under user's home) if possible 
        # and save it both to the Program attributes and user settings
        # compressedName = (Path('~') / outputFolder.relative_to(Path.home())).as_posix()
        #self.Attributes.add(Const.ATTR_GROUP, Const.ATTR_COMPRESSED_NAME, compressedName)
        #Settings.Set(Settings.OUTPUT_FOLDER, compressedName)
        Settings.Set(Settings.OUTPUT_FOLDER, outputFolder.as_posix())

        Settings.Save(self._attributes)
        
        #self._outputFolder = compressedName
        self._outputFolder = outputFolder