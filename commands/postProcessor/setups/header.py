from __future__ import annotations

import io
from pathlib import Path
from typing import Optional, TextIO, Union, overload

from ....lib.fusionAddInUtils.general_utils import Utils

from ..config import CMD_NAME
from ....config import PLUGIN_VERSION

from ..settings.settings import Settings
from .setup import Setup
from ..line import Line


class SetupsHeader(Line):
    #region GenerateHeader code
    # Type signatures for tools hints
    @overload
    @classmethod
    def WriteHeader(cls, fileHandler: TextIO, lineNumber: int) -> int: ...

    @overload
    @classmethod
    def WriteHeader(cls, folderPath: Path, lineNumber: int, fileName: Optional[str] = None, fileExtension: Optional[str] = None) -> int: ...
    @classmethod
    def WriteHeader(cls, pathOrFile: Union[Path, TextIO], lineNumber: int, fileName: Optional[str] = None, fileExtension: Optional[str] = None) -> int:

        fileHandlerParam: Optional[TextIO] = None

        # We got a file handler, so write directly to it.
        if isinstance(pathOrFile, io.TextIOBase):
            fileHandlerParam: TextIO = pathOrFile
            fileHandler: TextIO = fileHandlerParam
        # We got a path
        elif isinstance(pathOrFile, Path):
            pathParam: Path = pathOrFile
        else:
            raise TypeError("First argument must be either a file handler or a folder path.")

        try:
            firstSetup = next((setup for setup in cls.selected), None)

            if firstSetup is None: # No setups, exit early
                return lineNumber

            # For a single file output, there is only one header.
            if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SINGLE_FILE:
                lineNumber = cls._writeHeaderStart(fileHandler, firstSetup)
                for setup in cls.selected:
                    lineNumber = setup.WriteToolComment(fileHandler, lineNumber)
                lineNumber = firstSetup.WriteHeaderEnd(fileHandler, lineNumber)
            else: # For multiple files, write a header for each setup
                for setup in cls.selected:
                    if fileHandlerParam is None: # Create local file handler
                        fileHandler = cls._getFileHandler(cls.FileModes.WRITE, pathParam, fileName, setup, fileExtension)

                    lineNumber = cls._writeHeaderStart(fileHandler, setup)
                    lineNumber = setup.WriteToolComment(fileHandler, lineNumber)
                    lineNumber = setup.WriteHeaderEnd(fileHandler, lineNumber)

            return lineNumber

        finally:
            if fileHandlerParam is None and fileHandler is not None: # local filehandler was opened, so close it
                fileHandler.close()

    @classmethod
    def _writeHeaderStart(cls, fileHandler: TextIO, setup: Setup) -> int:
        path = Path(fileHandler.name)
        lineNumber = cls._writeLine(fileHandler, f"({path.stem})", 0) # Always start at 0 in a new header file
        lineNumber = cls._writeLine(fileHandler, f"(Generated with {CMD_NAME} version {PLUGIN_VERSION})", lineNumber)
        lineNumber = setup.WriteHeaderStart(fileHandler, lineNumber)
        return lineNumber
