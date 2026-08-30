from typing import TextIO

from .operation_context import OperationContext
from .analysis import parsed_operation

from ...file_modes import FileModes


def writeTail(
    ctx: OperationContext,
    fileHandle: TextIO,
):
    analysis = parsed_operation(ctx)

    if analysis.tail is None:
        return

    with analysis.source_file.open(FileModes.READ) as operationFile:
        line = operationFile.readline()
        row = 0
        while len(line) != 0:
            if row == analysis.tail.start: # Add an extra line marking where this operation tail starts
                if analysis.allow_blank_lines:
                    ctx.write(fileHandle, "\n") # ensure blank line before operation tail
                ctx.writeLine(fileHandle, f"({ctx.name})")
            if analysis.tail.contains(row):
                ctx.write(fileHandle, line)
            line = operationFile.readline()
            row += 1
