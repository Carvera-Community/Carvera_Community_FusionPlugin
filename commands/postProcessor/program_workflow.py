from pathlib import Path
from typing import Any

from .output_plan import plan_output_files
from .output_renderer import render_output_files
from .program_output import (
    ProgramOutputSettings,
    planProgramOutput,
    prepareOutputFolder,
)


def render_program_output(
    context: Any,
    output_path: Path,
    output_file_name: str | None,
    file_extension: str,
) -> bool:
    """Plan and stream every result file for one processing context."""
    settings = context.processingSettings or context.captureProcessingSettings()
    output_settings = ProgramOutputSettings(
        operationsGrouping=settings.operationsGrouping,
        flatFileStructure=settings.flatFileStructure,
        numericName=settings.numericName,
        clearFolder=settings.clearFolder,
    )
    if not prepareOutputFolder(output_path, output_settings.clearFolder):
        return False

    context.setFileExtension(file_extension)
    layout = planProgramOutput(output_path, output_file_name, output_settings)
    context.setPath(layout.path)
    context.setFileName(layout.fileName)

    plans = plan_output_files(context, settings, context.sanitizeFilename)
    render_output_files(plans, settings.overwriteFiles)
    return True
