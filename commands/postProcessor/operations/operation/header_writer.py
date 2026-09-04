from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from .....config import PLUGIN_VERSION
from ...config import CMD_NAME
from ...file_modes import FileModes
from .operation_context import OperationContext
from .analysis import parsed_operation


@dataclass(frozen=True)
class HeaderWriterSettings:
    restoreRapidMoves: bool
    rapidMovesMaxSteps: int
    rapidMovesMinimumDistance: float

    @classmethod
    def from_processing_settings(cls, settings) -> "HeaderWriterSettings":
        return cls(
            settings.restoreRapidMoves,
            settings.rapidMovesMaxSteps,
            settings.rapidMovesMinimumDistance,
        )

def write_header_start(
    ctx: OperationContext,
    fileHandle: TextIO,
    settings: HeaderWriterSettings | None = None,
):
    analysis = parsed_operation(ctx)
    if settings is None:
        if ctx.processingSettings is None:
            raise ValueError("Header writer settings are required")
        settings = HeaderWriterSettings.from_processing_settings(ctx.processingSettings)
    with analysis.source_file.open("r") as tempFile:
        
        file = Path(fileHandle.name).stem
        ctx.write_line(fileHandle, "({fileName})".format(fileName = file))
        ctx.write_line(fileHandle, "(Generated with {pluginName} version {pluginVersion})".format(pluginName = CMD_NAME, pluginVersion = PLUGIN_VERSION))
        if settings.restoreRapidMoves:
            ctx.write_line(fileHandle, "(Restore rapid moves enabled: {restoreRapidMoves}, maximum steps inbetween start and stop: {maximumSteps}, minimum travel distance: {minimumDistance}mm)".format(
                restoreRapidMoves = settings.restoreRapidMoves,
                maximumSteps = settings.rapidMovesMaxSteps,
                minimumDistance = settings.rapidMovesMinimumDistance
            ))
        line = tempFile.readline()
        row = 0

        while len(line) != 0:
            # It's the temporary file name, so ignore it as the 
            # real name has already been written.
            if line == f"({analysis.source_file.stem})\n":
                line = tempFile.readline()
                row += 1
                continue
            elif row == analysis.tool_comment_line:
                break
            ctx.write(fileHandle, line)
            line = tempFile.readline()
            row += 1

def write_tool_comment(context: OperationContext, fileHandle: TextIO):
    analysis = parsed_operation(context)
    if analysis.tool_comment_line is None:
        return
    with analysis.source_file.open(FileModes.READ) as operationFile:
        line = operationFile.readline()
        row = 0
        while len(line) != 0:
            if row == analysis.tool_comment_line:
                context.write(fileHandle, line)
                break
            line = operationFile.readline()
            row += 1

def write_header_end(ctx: OperationContext, fileHandle: TextIO):
    analysis = parsed_operation(ctx)
    if analysis.header is None:
        return
    tool_comment_line = analysis.tool_comment_line
    with analysis.source_file.open(FileModes.READ) as operationFile:
        line = operationFile.readline()
        row = 0
        while len(line) != 0:
            if row > (-1 if tool_comment_line is None else tool_comment_line) and analysis.header.contains(row):
                ctx.write(fileHandle, line)
            line = operationFile.readline()
            row += 1

def write_header(
    context: OperationContext,
    fileHandle: TextIO,
    settings: HeaderWriterSettings | None = None,
):
    write_header_start(context, fileHandle, settings)
    write_tool_comment(context, fileHandle)
    write_header_end(context, fileHandle)
