from __future__ import annotations

import io
from pathlib import Path
from typing import Optional, TextIO, Union, overload

from ...lib.fusionAddInUtils.general_utils import Utils

from .config import CMD_NAME
from ...config import PLUGIN_VERSION

from .settings import Settings
from .setup import Setup
from .line import Line


class SetupsHeader(Line):
    #region GenerateHeader code
    # Type signatures for tools hints
    @overload
    @classmethod
    def WriteHeader(cls, fileHandler: TextIO, lineNumber: int, addLineNumbers: bool, digits: int) -> int: ...

    @overload
    @classmethod
    def WriteHeader(cls, folderPath: Path, lineNumber: int, addLineNumbers: bool, digits: int, fileName: Optional[str] = None, fileExtension: Optional[str] = None) -> int: ...

    @classmethod
    def WriteHeader(cls, pathOrFile: Union[Path, TextIO], lineNumber: int, addLineNumbers: bool, digits: int, fileName: Optional[str] = None, fileExtension: Optional[str] = None) -> int:

        fileHandlerParam: Optional[TextIO] = None

        # We got a file handler, so write directly to it.
        if isinstance(pathOrFile, io.TextIOBase):
            fileHandlerParam: TextIO = pathOrFile
            fileHandler: TextIO = fileHandlerParam
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
                lineNumber = cls._writeHeader(fileHandler, lineNumber, addLineNumbers, digits, firstSetup)
                for setup in cls.selected:
                    lineNumber = setup.WriteToolComment(fileHandler, addLineNumbers, lineNumber, digits)
                lineNumber = firstSetup.WriteHeaderEnd(fileHandler, addLineNumbers, lineNumber, digits)
            else: # For multiple files, write a header for each setup
                for setup in cls.selected:
                    if Settings(Settings.FLAT_FILE_STRUCTURE):
                        path = pathParam
                    else:
                        path = pathParam / Utils.sanitizeFilename(setup.name, preserveExtension = False)
                        path.mkdir(parents=True, exist_ok=True)

                    if fileHandlerParam is None: # Create local file handler
                        fileHandler = cls._getFileHandler(cls.FileModes.APPEND, path, fileName, setup.name, fileExtension)

                    lineNumber = cls._writeHeader(fileHandler, lineNumber, addLineNumbers, digits, setup)
                    lineNumber = setup.WriteToolComment(fileHandler, addLineNumbers, lineNumber, digits)
                    lineNumber = setup.WriteHeaderEnd(fileHandler, addLineNumbers, lineNumber, digits)

            return lineNumber

        finally:
            if fileHandlerParam is None and fileHandler is not None: # local filehandler was opened, so close it
                fileHandler.close()

    @classmethod
    def _writeHeader(cls, fileHandler: TextIO, lineNumber: int, addLineNumbers: bool, digits: int, setup: Setup) -> int:
        path = Path(fileHandler.name)
        lineNumber = cls._writeLine(fileHandler, f"({path.stem})", lineNumber, addLineNumbers, digits)
        lineNumber = cls._writeLine(fileHandler, f"(Generated with {CMD_NAME} version {PLUGIN_VERSION})", lineNumber, addLineNumbers, digits)
        lineNumber = setup.WriteHeaderStart(fileHandler, addLineNumbers, lineNumber, digits)
        return lineNumber
