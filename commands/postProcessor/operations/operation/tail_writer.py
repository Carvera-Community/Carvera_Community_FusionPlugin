from dataclasses import dataclass
from typing import Protocol, TextIO

from .operation_context import OperationContext

from ...file_modes import FileModes


class FileNameTarget(Protocol):
    @property
    def fileName(self) -> str | None: ...

    def SetFileName(self, fileName: str) -> None: ...


@dataclass(frozen=True)
class TailWriterSettings:
    numericName: bool
    fileSequenceDigits: int

    @classmethod
    def fromProcessingSettings(cls, settings) -> "TailWriterSettings":
        return cls(settings.numericName, settings.fileSequenceDigits)

    @classmethod
    def fromCurrentSettings(cls) -> "TailWriterSettings":
        from ...settings.settings import Settings

        return cls(
            numericName=bool(Settings.Get(Settings.NUMERIC_NAME)),
            fileSequenceDigits=Settings.Get(Settings.FILE_SEQUENCE_DIGITS),
        )


def writeTail(
    ctx: OperationContext,
    fileHandle: TextIO,
    settings: TailWriterSettings | None = None,
    fileNameTarget: FileNameTarget | None = None,
):
    settings = settings or (
        TailWriterSettings.fromProcessingSettings(ctx.processingSettings)
        if ctx.processingSettings is not None
        else TailWriterSettings.fromCurrentSettings()
    )

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
    if (
        settings.numericName
        and fileNameTarget is not None
        and fileNameTarget.fileName is not None
        and fileNameTarget.fileName.isnumeric()
    ):
        fileNameTarget.SetFileName(
            str(int(fileNameTarget.fileName) + 1).rjust(settings.fileSequenceDigits, "0")
        )
