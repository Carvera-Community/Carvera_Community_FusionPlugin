from pathlib import Path
from typing import TextIO

from .....config import PLUGIN_VERSION
from ...settings.settings import Settings
from ...config import CMD_NAME
from ...file_modes import FileModes
from .operation_context import OperationContext

def writeHeaderStart(ctx: OperationContext, fileHandle: TextIO):
    with ctx.tempFilePath.open("r") as tempFile:
        
        file = Path(fileHandle.name).stem
        ctx.writeLine(fileHandle, "({fileName})".format(fileName = file))
        ctx.writeLine(fileHandle, "(Generated with {pluginName} version {pluginVersion})".format(pluginName = CMD_NAME, pluginVersion = PLUGIN_VERSION))
        if Settings(Settings.RESTORE_RAPID_MOVES):
            ctx.writeLine(fileHandle, "(Restore rapid moves enabled: {restoreRapidMoves}, maximum steps inbetween start and stop: {maximumSteps}, minimum travel distance: {minimumDistance}mm)".format(
                restoreRapidMoves = Settings(Settings.RESTORE_RAPID_MOVES),
                maximumSteps = Settings(Settings.RAPID_MOVES_MAX_STEPS),
                minimumDistance = Settings(Settings.RAPID_MOVES_MINIMUM_DISTANCE)
            ))
        line = tempFile.readline()
        row = 0

        while len(line) != 0:
            # It's the temporary file name, so ignore it as the 
            # real name has already been written.
            if line == f"({ctx.tempFilePath.stem})\n": 
                line = tempFile.readline()
                row += 1
                continue
            elif row == ctx.toolCommentLine:
                break
            ctx.write(fileHandle, line)
            line = tempFile.readline()
            row += 1

def writeToolComment(context: OperationContext, fileHandle: TextIO):
    with context.tempFilePath.open(FileModes.READ) as operationFile:
        line = operationFile.readline()
        row = 0
        while len(line) != 0:
            if row == context.toolCommentLine:
                context.write(fileHandle, line)
                break
            line = operationFile.readline()
            row += 1

def writeHeaderEnd(ctx: OperationContext, fileHandle: TextIO):
    with ctx.tempFilePath.open(FileModes.READ) as operationFile:
        line = operationFile.readline()
        row = 0
        while len(line) != 0:
            if row > ctx.toolCommentLine and row <= ctx.headerEndLine:
                ctx.write(fileHandle, line)
            line = operationFile.readline()
            row += 1

def writeHeader(context: OperationContext, fileHandle: TextIO):
    writeHeaderStart(context, fileHandle)
    writeToolComment(context, fileHandle)
    writeHeaderEnd(context, fileHandle)

