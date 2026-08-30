from pathlib import Path
from typing import Any

from .output_plan import plan_output_files
from .output_renderer import render_output_files
from .program_output import (
    ProgramOutputSettings,
    plan_program_output,
    prepare_output_folder,
)


def render_program_output(
    context: Any,
    output_path: Path,
    output_file_name: str | None,
    file_extension: str,
) -> None:
    """Plan and stream every result file for one processing context."""
    settings = context.processingSettings or context.captureProcessingSettings()
    output_settings = ProgramOutputSettings(
        operationsGrouping=settings.operationsGrouping,
        flatFileStructure=settings.flatFileStructure,
        numericName=settings.numericName,
        clearFolder=settings.clearFolder,
    )
    prepare_output_folder(output_path, output_settings.clearFolder)

    context.setFileExtension(file_extension)
    layout = plan_program_output(output_path, output_file_name, output_settings)
    context.setPath(layout.path)
    context.setFileName(layout.fileName)

    plans = plan_output_files(context, settings, context.sanitizeFilename)
    render_output_files(plans, settings.overwriteFiles)
