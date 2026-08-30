from __future__ import annotations
from pathlib import Path
from typing import Any, Protocol, TYPE_CHECKING

from .strings import Strings
from .attributes import Attributes

from .parameters import Parameters
from .program_output import (
    ProgramOutputSettings,
    planProgramOutput,
    prepareOutputFolder,
)
from .output_plan import plan_output_files
from .output_renderer import render_output_files

if TYPE_CHECKING:
    from .setups.setups_context import SetupsContext


class ProgramFusionAdapter(Protocol):
    def machineHasATC(self, program) -> bool: ...
    def machineToolSlots(self, program) -> int: ...
    def machineHasAAxis(self, program) -> bool: ...
    def postProcess(self, program) -> bool: ...

class Program():
    def __init__(
        self,
        program: Any,
        fusionAdapter: ProgramFusionAdapter | None = None,
        parameterValueAdapter=None,
    ):
        if fusionAdapter is None:
            from .fusion_adapters.program import FusionProgramAdapter

            fusionAdapter = FusionProgramAdapter()
        self._fusionAdapter = fusionAdapter
        self._program = program
        self._outputFolder: Path | None = None
        self._attributes: Attributes = Attributes(program.attributes)
        self._parameters: Parameters = Parameters(
            program.parameters,
            parameterValueAdapter,
        )

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
    def parameters(self):
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
        return self._fusionAdapter.machineHasATC(self._program)
    
    @property
    def machineToolSlots(self):
        """Returns the number of ATC slots of the machine of the NCProgram."""
        return self._fusionAdapter.machineToolSlots(self._program)

    @property
    def machineHasAAxis(self):
        """Returns whether the machine has A axis."""

        return self._fusionAdapter.machineHasAAxis(self._program)
    
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
        return self.parameters.Get(Parameters.FILE_NAME, str)

    def set_file_name(self, fileName: str):
        """Sets the file name of the NCProgram."""
        self.parameters.Set(Parameters.FILE_NAME, fileName)

    @property
    def fileExtension(self):
        """Returns the file extension of the NCProgram."""
        return self._program.postConfiguration.extension if self._program.postConfiguration else None

    def process(self, ctx: "SetupsContext", tmpPath: Path):
        """Generate the initial G-code files from the Fusion NCProgram using the Post Processor 
            and gather information for generation of final files."""
        oldOutputFolder = self.get_output_folder()
        ctx.captureProcessingSettings()

        # TODO: Start showing progress here
        #endregion

        outputFolder = self.get_output_folder()
        fileName = self.fileName
        name = self.parameters.Get(Parameters.NAME, str)

        try:
            ctx.parse(tmpPath)
        finally:
            self.set_output_folder(outputFolder)
            if fileName is not None:
                self.parameters.Set(Parameters.FILE_NAME, fileName)
            if name is not None:
                self.parameters.Set(Parameters.NAME, name)

        # Restore the output folder in the NC Program parameters
        self.set_output_folder(oldOutputFolder)

    def write_output(self, ctx: "SetupsContext"):
        """Write the final G-code files from the results of the post processing."""
        initialPath = self.get_output_folder()
        initialFileName = self.fileName
        programName = self.parameters.Get(Parameters.NAME, str)

        try:
            current = ctx.processingSettings or ctx.captureProcessingSettings()
            outputSettings = ProgramOutputSettings(
                operationsGrouping=current.operationsGrouping,
                flatFileStructure=current.flatFileStructure,
                numericName=current.numericName,
                clearFolder=current.clearFolder,
            )
            if not prepareOutputFolder(initialPath, outputSettings.clearFolder):
                return  # Need to notify the user about this.
            
            # Setting the base parameters for the output.
            ctx.setFileExtension(self._program.postConfiguration.extension)
            outputLayout = planProgramOutput(
                initialPath,
                initialFileName,
                outputSettings,
            )
            ctx.setPath(outputLayout.path)
            ctx.setFileName(outputLayout.fileName)

            plans = plan_output_files(
                ctx,
                current,
                ctx.sanitizeFilename,
            )
            render_output_files(plans, current.overwriteFiles)

        finally:
            self.set_output_folder(initialPath)
            if initialFileName is not None:
                self.parameters.Set(Parameters.FILE_NAME, initialFileName)
            if programName is not None:
                self.parameters.Set(Parameters.NAME, programName)

    def disable_open_in_editor(self):
        """Convenience method for disabling "Open in Editor" option"""
        self.parameters.Set(Parameters.OPEN_IN_EDITOR, False)

    def post_process(self, operations):
        if len(operations) == 0:
            return False # Nothing to process
        self._program.operations = operations
        return self._fusionAdapter.postProcess(self._program)

    def set_output_folder(self, folder: Path):
        """Convenience method to set and verify output folder"""
        self.parameters.Set(Parameters.OUTPUT_FOLDER, folder.as_posix())
        result = self.get_output_folder()
        if result != folder and str(folder)[0:2] == "\\\\":
            self.parameters.Set(Parameters.OUTPUT_FOLDER, "\\\\" + str(folder))    # double up leading "\"
        return None

    def get_output_folder(self) -> Path:
        """Convenience method to get output folder"""
        return Path(str(self.parameters.Get(Parameters.OUTPUT_FOLDER, str)))
