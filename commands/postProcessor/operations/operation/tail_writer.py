from typing import TextIO

from .operation_context import OperationContext

from ...file_modes import FileModes

def writeTail(ctx: OperationContext, fileHandle: TextIO):

    with ctx.tempFilePath.open(FileModes.READ) as operationFile:
        line = operationFile.readline()
        row = 0
        while len(line) != 0:
            if row == ctx.tailStartLine: # Add an extra line marking where this operation tail starts
                if(ctx.allowBlankLines):
                    ctx.write(fileHandle, "\n") # ensure blank line before operation tail
                ctx.writeLine(fileHandle, f"({ctx.name})")
            if row >= ctx.tailStartLine:
                ctx.write(fileHandle, line)
            line = operationFile.readline()
            row += 1
    # For numeric file names
    from ...programs import Programs
    from ...settings.settings import Settings

    if (Settings(Settings.NUMERIC_NAME) 
        and Programs.Current is not None 
        and Programs.Current.fileName is not None 
        and Programs.Current.fileName.isnumeric()):
        Programs.Current.SetFileName(str(int(Programs.Current.fileName) + 1).rjust(Settings(Settings.FILE_SEQUENCE_DIGITS), '0'))
