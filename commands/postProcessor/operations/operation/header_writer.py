from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from .....config import PLUGIN_VERSION
from ...settings.settings import Settings
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
    def fromProcessingSettings(cls, settings) -> "HeaderWriterSettings":
        return cls(
            settings.restoreRapidMoves,
            settings.rapidMovesMaxSteps,
            settings.rapidMovesMinimumDistance,
        )

    @classmethod
    def fromCurrentSettings(cls) -> "HeaderWriterSettings":
        return cls(
            restoreRapidMoves=bool(Settings.Get(Settings.RESTORE_RAPID_MOVES)),
            rapidMovesMaxSteps=Settings.Get(Settings.RAPID_MOVES_MAX_STEPS),
            rapidMovesMinimumDistance=Settings.Get(
                Settings.RAPID_MOVES_MINIMUM_DISTANCE
            ),
        )


def writeHeaderStart(
    ctx: OperationContext,
    fileHandle: TextIO,
    settings: HeaderWriterSettings | None = None,
):
    analysis = parsed_operation(ctx)
    settings = settings or (
        HeaderWriterSettings.fromProcessingSettings(ctx.processingSettings)
        if ctx.processingSettings is not None
        else HeaderWriterSettings.fromCurrentSettings()
    )
    with analysis.source_file.open("r") as tempFile:
        
        file = Path(fileHandle.name).stem
        ctx.writeLine(fileHandle, "({fileName})".format(fileName = file))
        ctx.writeLine(fileHandle, "(Generated with {pluginName} version {pluginVersion})".format(pluginName = CMD_NAME, pluginVersion = PLUGIN_VERSION))
        if settings.restoreRapidMoves:
            ctx.writeLine(fileHandle, "(Restore rapid moves enabled: {restoreRapidMoves}, maximum steps inbetween start and stop: {maximumSteps}, minimum travel distance: {minimumDistance}mm)".format(
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

def writeToolComment(context: OperationContext, fileHandle: TextIO):
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

def writeHeaderEnd(ctx: OperationContext, fileHandle: TextIO):
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

def writeHeader(
    context: OperationContext,
    fileHandle: TextIO,
    settings: HeaderWriterSettings | None = None,
):
    writeHeaderStart(context, fileHandle, settings)
    writeToolComment(context, fileHandle)
    writeHeaderEnd(context, fileHandle)
