from __future__ import annotations
import os
import shutil
from adsk import cam
from pathlib import Path

from .strings import Strings
from .attributes import Attributes

from .setups.setups_context import SetupsContext 
from .setups.header_writer import writeHeader as writeSetupsHeader
from .setups.body_writer import writeBody as writeSetupsBody
from .setups.tail_writer import writeTail as writeSetupsTail

from .settings.settings import Settings
from .parameters import Parameters

class Program():
    def __init__(self, program: cam.NCProgram):
        self._program: cam.NCProgram = program
        self._outputFolder: Path | None = None
        self._attributes: Attributes = Attributes(program.attributes)
        self._parameters: Parameters = Parameters(program.parameters)

    @property
    def name(self):
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
    def hasMachine(self):
        """Returns whether the NCProgram has a machine."""
        return self._program.machine is not None

    @property
    def machineName(self) -> str:
        """Returns the machine of the NCProgram."""
        return self._program.machine.model if self.hasMachine else Strings("<no machine selected>")

    @property
    def machineHasATC(self):
        """Returns whether the machine of the NCProgram has an ATC."""
        return cam.ToolingCapabilitiesMachineElement.cast(self._program.machine.elements.itemById('tooling','default')).isToolChangerAutomatic if self.hasMachine else False
    
    @property
    def machineToolSlots(self):
        """Returns the number of ATC slots of the machine of the NCProgram."""
        return cam.ToolingCapabilitiesMachineElement.cast(self._program.machine.elements.itemById('tooling','default')).maxToolCount if self.machineHasATC else 1

    @property
    def machineHasAAxis(self):
        """Returns whether the machine has A axis."""

        machine = self._program.machine

        if machine is None:
            return False

        axes = cam.ControllerConfigurationMachineElement.cast(
            machine.elements.defaultItemByType('controller')).axisConfigurations

        for index in range(axes.count):
            try:
                axis = axes.item(index)
            except RuntimeError as error:
                if index >= 3 and 'axisDefinition' in str(error):
                    unreadable_extra_axis = True
                    continue
                raise

            if cam.RotaryMachineAxisConfiguration.cast(axis) is not None:
                return True

        return unreadable_extra_axis
    
    @property
    def hasPostProcessor(self):
        """Returns whether the NCProgram has a post processor."""
        return self._program.postConfiguration is not None

    @property
    def postProcessorDescription(self):
        """Returns the post processor of the current NCProgram."""
        return self._program.postConfiguration.description if self.hasPostProcessor else Strings("<no post processor selected>")
    
    @property
    def fileName(self):
        """Returns the file name of the NCProgram."""
        return self.Parameters.Get(Parameters.FILE_NAME, str)

    def SetFileName(self, fileName: str):
        """Sets the file name of the NCProgram."""
        self.Parameters.Set(Parameters.FILE_NAME, fileName)

    @property
    def fileExtension(self):
        """Returns the file extension of the NCProgram."""
        return self._program.postConfiguration.extension if self._program.postConfiguration else None

    def Process(self, ctx: SetupsContext, tmpPath: Path):
        """Generate the initial G-code files from the Fusion NCProgram using the Post Processor 
            and gather information for generation of final files."""
        oldOutputFolder = self.GetOutputFolder()

        # TODO: Start showing progress here
        #endregion

        outputFolder = self.GetOutputFolder()
        fileName = self.fileName
        name = self.Parameters.Get(Parameters.NAME, str)

        try:
            ctx.parse(tmpPath)
        finally:
            self.SetOutputFolder(outputFolder)
            if fileName is not None:
                self.Parameters.Set(Parameters.FILE_NAME, fileName)
            if name is not None:
                self.Parameters.Set(Parameters.NAME, name)

        # Restore the output folder in the NC Program parameters
        self.SetOutputFolder(oldOutputFolder)

    def WriteOutput(self, ctx: SetupsContext):
        """Write the final G-code files from the results of the post processing."""
        initialPath = self.GetOutputFolder()
        initialFileName = self.fileName
        programName = self.Parameters.Get(Parameters.NAME, str)

        try:
            if initialPath.exists() and not initialPath.is_dir():
                return # Need to notify the user about this.

            if Settings(Settings.CLEAR_FOLDER) and initialPath.exists() and initialPath.is_dir():
                for child in initialPath.iterdir():
                    try:
                        if child.is_dir() and not child.is_symlink():
                            shutil.rmtree(child)
                        else:
                            child.unlink()
                    except Exception:
                        return # File/folder could not be deleted, likely due to permissions. Need to notify the user about this.
            
            # Setting the base parameters for the output.
            ctx.setFileExtension(self._program.postConfiguration.extension)
            if (Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SINGLE_FILE 
                or Settings(Settings.FLAT_FILE_STRUCTURE) 
                or (Settings(Settings.NUMERIC_NAME) 
                    and initialFileName is not None 
                    and initialFileName.isnumeric())): # numeric name is a special case where we want to keep a single file name and just increment it, so we treat it like single file grouping even if the user has selected otherwise
                # Flat file structure / single file / numeric filename
                ctx.setPath(initialPath)
                ctx.setFileName(str(initialFileName))
            else:
                ctx.setPath(initialPath / str(initialFileName))

            writeSetupsHeader(ctx)

            if Settings(Settings.NUMERIC_NAME) and initialFileName is not None and initialFileName.isnumeric():
                ctx.setFileName(initialFileName) # Reset the numeric name
            writeSetupsBody(ctx)

            if Settings(Settings.NUMERIC_NAME) and initialFileName is not None and initialFileName.isnumeric():
                ctx.setFileName(initialFileName) # Reset the numeric name
            writeSetupsTail(ctx)

        except Exception as exc:
            raise exc
        finally:
            self.SetOutputFolder(initialPath)
            if initialFileName is not None:
                self.Parameters.Set(Parameters.FILE_NAME, initialFileName)
            if programName is not None:
                self.Parameters.Set(Parameters.NAME, programName)

    def DisableOpenInEditor(self):
        """Convenience method for disabling "Open in Editor" option"""
        self.Parameters.Set(Parameters.OPEN_IN_EDITOR, False)

    def PostProcess(self, operations):
        if len(operations) == 0:
            return False # Nothing to process
        self._program.operations = operations
        return self._program.postProcess(cam.NCProgramPostProcessOptions.create())

    def SetOutputFolder(self, folder: Path):
        """Convenience method to set and verify output folder"""
        self.Parameters.Set(Parameters.OUTPUT_FOLDER, folder.as_posix())
        result = self.GetOutputFolder()
        if result != folder and str(folder)[0:2] == "\\\\":
            self.Parameters.Set(Parameters.OUTPUT_FOLDER, "\\\\" + str(folder))    # double up leading "\"
        return None

    def GetOutputFolder(self) -> Path:
        """Convenience method to get output folder"""
        return Path(str(self.Parameters.Get(Parameters.OUTPUT_FOLDER, str)))
