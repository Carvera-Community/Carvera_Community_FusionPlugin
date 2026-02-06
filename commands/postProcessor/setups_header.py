from __future__ import annotations

import io
from pathlib import Path
from typing import Optional, TextIO, overload

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
    def WriteHeader(cls, folderPath: Path, lineNumber: int, addLineNumbers: bool, digits: int, fileExtension: str) -> int: ...

    @classmethod
    def WriteHeader(cls, pathOrFile: TextIO, lineNumber: int, addLineNumbers: bool, digits: int, fileExtension: Optional[str] = None) -> int:

        fileHandlerParam: Optional[TextIO] = None

        if isinstance(pathOrFile, io.TextIOBase):
            fileHandlerParam: TextIO = pathOrFile
            fileHandler: TextIO = fileHandlerParam

        try:
            firstSetup = next((setup for setup in cls.selected), None)

            if firstSetup is None: # No setups, exit early
                return lineNumber

            # For a single file output, there is only one header.
            if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SINGLE_FILE:
                if fileHandlerParam is None: fileHandler = cls._getFileHandler(cls.FileModes.WRITE, pathOrFile, '', firstSetup.name, fileExtension)
                lineNumber = cls._writeHeader(fileHandler, lineNumber, addLineNumbers, digits, firstSetup)

            for setup in cls.selected:
                # One header per setup
                if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SETUP:
                    if fileHandlerParam is None: fileHandler = cls._getFileHandler(cls.FileModes.WRITE, pathOrFile, '', setup.name, fileExtension)
                    lineNumber = cls._writeHeader(fileHandler, lineNumber, addLineNumbers, digits, setup)

                # Put the tool comments in the header file we're working on at the moment
                if fileHandlerParam is None: fileHandler = cls._getFileHandler(cls.FileModes.APPEND, pathOrFile, '', setup.name, fileExtension)
                lineNumber = setup.WriteToolComment(fileHandler, addLineNumbers, lineNumber, digits)

                # If grouping by setup, also write the header end in the same file after the tool comments
                if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SETUP:
                    if fileHandlerParam is None: fileHandler = cls._getFileHandler(cls.FileModes.APPEND, pathOrFile, '', setup.name, fileExtension)
                    lineNumber = setup.WriteHeaderEnd(fileHandler, addLineNumbers, lineNumber, digits)

            # If writing to a single file, write the header end after all tool comments have been written for all setups
            if Settings(Settings.OPERATIONS_GROUPING) == Settings.OperationsGroupings.SINGLE_FILE:
                if fileHandlerParam is None: fileHandler = cls._getFileHandler(cls.FileModes.APPEND, pathOrFile, '', firstSetup.name, fileExtension)
                lineNumber = firstSetup.WriteHeaderEnd(fileHandler, addLineNumbers, lineNumber, digits)

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
