from dataclasses import dataclass
from typing import Protocol, TextIO

from .operation_context import OperationContext
from .analysis import parsed_operation

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
    analysis = parsed_operation(ctx)
    settings = settings or (
        TailWriterSettings.fromProcessingSettings(ctx.processingSettings)
        if ctx.processingSettings is not None
        else TailWriterSettings.fromCurrentSettings()
    )

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
    if (
        settings.numericName
        and fileNameTarget is not None
        and fileNameTarget.fileName is not None
        and fileNameTarget.fileName.isnumeric()
    ):
        fileNameTarget.SetFileName(
            str(int(fileNameTarget.fileName) + 1).rjust(settings.fileSequenceDigits, "0")
        )
