import io
from pathlib import Path
import re
import tempfile
import time
from typing import TYPE_CHECKING, Final, Optional, TextIO, overload
import uuid
import uuid

if TYPE_CHECKING:
    from .operations import Operations

from .settings import Settings
from .parameters import Parameters

class Operation:
    _BODY_RE: Final = re.compile(r""
        r"(?P<N>N[0-9]+ *)?" # line number
        r"(?P<line>"         # line w/o number
        r"(M(?P<M>[0-9]+) *)?" # M-code
        r"(G(?P<G>[0-9]+) *)?" # G-code
        r"(T(?P<T>[0-9]+))?" # Tool
        r".+)",              # to end of line
        re.IGNORECASE | re.DOTALL)
    
    # _PARSE_LINE_RE: Final = re.compile(r""
    #         r"(G(?P<G>[0-9]+(\.[0-9]*)?)[^XYZF]*)?"
    #         r"(?P<XY>((X-?[0-9]+(\.[0-9]*)?)[^XYZF]*)?"
    #         r"((Y-?[0-9]+(\.[0-9]*)?)[^XYZF]*)?)"
    #         r"(Z(?P<Z>-?[0-9]+(\.[0-9]*)?)[^XYZF]*)?"
    #         r"(F(?P<F>-?[0-9]+(\.[0-9]*)?)[^XYZF]*)?",
    #         re.IGNORECASE)

    _PARSE_LINE_RE: Final = re.compile(r""
            r"(G(?P<G>[0-9]+(\.[0-9]*)?)[^XYZFA]*)?"
            r"(?P<XY>((X-?[0-9]+(\.[0-9]*)?)[^XYZFA]*)?((Y-?[0-9]+(\.[0-9]*)?)[^XYZFA]*)?)"
            r"(A(?P<A>-?[0-9]+(\.[0-9]*)?)[^XYZFA]*)?"
            r"(Z(?P<Z>-?[0-9]+(\.[0-9]*)?)[^XYZFA]*)?"
            r"(F(?P<F>-?[0-9]+(\.[0-9]*)?)[^XYZFA]*)?",
            re.IGNORECASE)
    
    _GCODES_RE: Final = re.compile(r"G([0-9]+(?:\.[0-9]*)?)")

    _TOOL_COMMENT_REG: Final = re.compile(r"\((T[0-9])+\s")

    _COMMENT_REG: Final = re.compile(r"^(?:\s*)\((.*)\)(?:\s*)$")


    def __init__(self):
        self._outputFileName = None
        # As there can be multiple operations without tools they are 
        # grouped with the previous operation (or next if it is the 
        # first operation missing a tool)
        self._operationsList = [] 
        self._operationWithTool = None
        self._tempFilePath: Path = None
        self._allowBlankLines = False
        self._headerGenerated = False
        self._rotationLine = 0

    def Append(self, operation, hasTool):
        self._operationsList.append(operation)
        if hasTool:
            self._operationWithTool = operation

    @property
    def toolId(self):
        return Operations.GetToolNumber(self._operationWithTool) if self.hasTool else None

    @property
    def hasTool(self):
        return self._operationWithTool is not None and self._operationWithTool.hasToolpath

    @property
    def name(self):
        return self._operationWithTool.name if self._operationWithTool is not None else "NoToolOperation"

    @property
    def tempFilePath(self) -> Path:
        return self._tempFilePath
    
    @property
    def hasBody(self) -> bool:
        return self._bodyStartLine != -1
    
    @property
    def hasTail(self) -> bool:
        return self._tailStartLine != -1
    
    @property
    def hasRotation(self) -> bool:
        return self._rotationLine != 0

    @property
    def headerGenerated(self) -> bool:
        return self._headerGenerated

    def SetOutputFolder(self, folder: Path):
        self._outputFilePath = folder

    def SetOutputFileName(self, fileName):
        self._outputFileName = fileName

    def Parse(self, tmpPath: Path):
        from .programs import Programs

        name = uuid.uuid4().hex + Programs.Current.fileExtension
        self._tempFilePath = tmpPath / name

        Programs.Current.SetOutputFolder(self._tempFilePath.parent)
        Programs.Current.Parameters.Set(Parameters.FILE_NAME, self._tempFilePath.stem)
        Programs.Current.Parameters.Set(Parameters.NAME, self._tempFilePath.stem)
        if not Programs.Current.PostProcess(self._operationsList):
            raise Exception(f"Operation {self.name} post processing failed.")
        time.sleep(0.1) # files missing sometimes unless we slow down (??)

        self._parseFile(self._tempFilePath)

    def _parseFile(self, filePath: Path):
        #region Header example
        # Find the start of the header and body in the generated file

        # Parse the gcode. We expect a header like this:
        #
        # % <optional>
        # (<comments>) <0 or more lines>
        # (<Txx tool comment>) <optional>
        # <comments or G-code initialization, up to Txx>
        #
        # This header is stripped from all files after the first,
        # except the tool comment is put in a list at the top.
        # The header ends when we find the body, which starts with:
        #
        # Txx ...   (optionally preceded by line number Nxx)
        #
        # We copy all the body, looking for the tail. The start
        # of the tail is denoted by any of a list of G-codes
        # entered by the user. The defaults are:
        # M30 - end program
        # M5 - stop spindle
        # M9 - stop coolant
        # The tail is stripped until the last operation is done.
        #endregion

        with filePath.open("r") as operationFile:
            line = operationFile.readline()
            self._toolCommentLine = -1
            lineNumber = -1
            inHeader = False
            processHeader = True
            processBody = False
            while len(line) != 0:
                lineNumber += 1

                if not self._allowBlankLines and line[0] == "\n":
                    self._allowBlankLines = True

                if processHeader:
                    processHeader, inHeader = self._parseHeaderLine(line, lineNumber, inHeader)
                    processBody = not processHeader
                elif processBody:
                    if self._parseBodyLine(line, lineNumber):
                        return
                line = operationFile.readline()
        return # No tail found, so probably a handmade operation

    def _parseHeaderLine(self, line: str, lineNumber: int, inHeader: bool) -> tuple[bool, bool]:
        toolComment = self._TOOL_COMMENT_REG.search(line)
        if toolComment: # We have found the tool comment line
            self._toolCommentLine = lineNumber
        else:
            headerMatch = self._BODY_RE.match(line)
            if headerMatch:
                if headerMatch.group("G") is not None:
                    # Found a g-code, check if it is
                    # in the list of header end codes
                    if f"G{headerMatch.group('G')}" in Settings.Get(Settings.HEADER_END_CODES):
                        # Found the end of the header
                        self._headerEndLine = lineNumber
                        inHeader = True
                elif headerMatch.group("M") is not None:
                    # Found an m-code, check if it is
                    # in the list of header end codes
                    if f"M{headerMatch.group('M')}" in Settings.Get(Settings.HEADER_END_CODES):
                        # Found the end of the header
                        self._headerEndLine = lineNumber
                        inHeader = True
                elif inHeader or headerMatch.group("T") is not None:
                    # Definitely found the body as this is
                    # either a tool change line or a line
                    # not in header end codes, so we're done
                    self._bodyStartLine = lineNumber
                    return (False, inHeader)
        return (True, inHeader)

    def _parseBodyLine(self, line: str, lineNumber: int):
        bodyMatch = self._BODY_RE.match(line)
        if bodyMatch:
            if bodyMatch.group("G") is not None:
                gCode = int(bodyMatch.group("G"))
                if gCode == 0:
                    lineMatch = self._PARSE_LINE_RE.match(line)
                    # We're only interested in the first rotation move
                    if not self.hasRotation and lineMatch and lineMatch.group("G") is not None and lineMatch.group("A") is not None:
                        aCode = float(lineMatch.group("A"))
                        if aCode == 0.0:
                            # Found A-axis rotation move
                            self._rotationLine = lineNumber
            if bodyMatch.group("T") is not None:
                # found body start
                self._bodyStartLine = lineNumber
            elif bodyMatch.group("M") is not None:
                mCode = int(bodyMatch.group("M"))
                if f"M{mCode}" in Settings.Get(Settings.END_CODES):
                    # found tail start
                    self._tailStartLine = lineNumber
                    return True # File analysis complete
        return False

    #region GenerateHeader
    # Type signatures for tools (mypy/IDE) hints

    # If GenerateHeader is called with a fileHandler it means that the output
    # will only be one file
    @overload
    def GenerateHeader(self, fileHandler: TextIO, lineNumber: int, addLineNumbers: bool, digits: int, briefHeader: bool) -> int: ...

    # If GenerateHeader is called with folder it means that 
    # multiple files will be generated on lower levels of the hierarchy
    @overload
    def GenerateHeader(self, folderPath: Path, lineNumber: int, addLineNumbers: bool, digits: int, briefHeader: bool, fileName: str, fileExtension: str) -> int: ...

    # Runtime implementation of Generate
    def GenerateHeader(self, arg, lineNumber: int, addLineNumbers: bool, digits: int, briefHeader: bool, fileName: Optional[str] = None, fileExtension: Optional[str] = None) -> int:

        # case 1: given an open file (TextIO) means that everything 
        # should be written to it and no directory structure
        # should be created.
        if isinstance(arg, io.TextIOBase) and fileName is None and fileExtension is None:
            fileHandler: TextIO = arg

            with self._tempFilePath.open("r") as operationFile:
                line = operationFile.readline()
                row = 0
                while len(line) != 0:
                    # skip temporary file name line
                    if line == f"({self._tempFilePath.stem})\n": 
                        #fileHandler.write(f" - ignored header: {line}")
                        line = operationFile.readline()
                        row += 1
                        continue
                    if row == self._toolCommentLine:
                        lineNumber = self._write(fileHandler, line, lineNumber, addLineNumbers, digits)
                        if briefHeader: # We're done with the header here
                            break
                    elif row <= self._headerEndLine and not briefHeader:
                        lineNumber = self._write(fileHandler, line, lineNumber, addLineNumbers, digits)
                    #elif row < self._bodyStartLine:
                        #fileHandler.write(f" - ignored header: {line}")
                    else:
                        break

                    line = operationFile.readline()
                    row += 1
                self._headerGenerated = True
            return lineNumber
                
        # case 2: given folder + name + ext
        if isinstance(arg, Path) and fileName is not None and fileExtension is not None:
            folder: Path = arg
            folder.mkdir(parents=True, exist_ok=True)
            filename = f"{fileName}{fileExtension}"
            p = folder / filename
            # öppna och skriv via samma inre funktion
            with p.open("w", encoding="utf-8") as fh:
                self._generate_to_file(fh)
            return p

        raise TypeError("Call GenerateHeader(fileHandler) or GenerateHeader(folderPath, fileName, fileExtension)")
    #endregion

    #region GenerateBody
    # Type signatures for tools (mypy/IDE) hints

    # If GenerateBody is called with a fileHandler it means that the output
    # will only be one file
    @overload
    def GenerateBody(self, fileHandler: TextIO, lineNumber: int, addLineNumbers: bool, digits: int, *, rotationAngle: Optional[float] = None, preserveRotation: Optional[bool] = False) -> int: ...

    # If GenerateBody is called with folder it means that 
    # multiple files will be generated on lower levels of the hierarchy
    @overload
    def GenerateBody(self, folderPath: Path, lineNumber: int, addLineNumbers: bool, digits: int, fileName: str, fileExtension: str, *, rotationAngle: Optional[float] = None, preserveRotation: Optional[bool] = False) -> int: ...

    # Runtime implementation of Generate
    def GenerateBody(self, fileOrPath, lineNumber: int, addLineNumbers: bool, digits: int, fileName: Optional[str] = None, fileExtension: Optional[str] = None, *, rotationAngle: Optional[float] = None, preserveRotation: Optional[bool] = False) -> int:

        # case 1: given an open file (TextIO) means that everything 
        # should be written to it and not creating a new file
        if isinstance(fileOrPath, io.TextIOBase) and fileName is None and fileExtension is None:
            fileHandler: TextIO = fileOrPath
            # first line in the output, make sure that all lines above 
            # the tool comment is written as well.

            with self._tempFilePath.open("r") as operationFile:
                line = operationFile.readline()
                row = 0
                while len(line) != 0:
                    if row >= self._bodyStartLine:
                        if row == self._bodyStartLine: # Add an extra line marking where this operation starts
                            if self._allowBlankLines:
                                fileHandler.write('\n') # keep blank line before operation start
                            lineNumber = self._writeLine(fileHandler, f"({self.name} Start)", lineNumber, addLineNumbers, digits)
                        lineMatch = self._PARSE_LINE_RE.match(line)
                        if lineMatch:
                            if lineMatch.group("G") is not None and lineMatch.group("A") is not None:
                                gCode = lineMatch.group("G")
                                aCode = lineMatch.group("A")
                                # Special handling of A-axis rotation moves.
                                # The rotation will always be 0 as the operation
                                # are always generated one by one
                                if gCode == "0" and float(aCode) == 0.0 and row == self._rotationLine:
                                    if preserveRotation: # This is the first setup, so we want it to rotate to 0, so we keep the rotations as is
                                        pass
                                    elif rotationAngle is None: # No rotation provided, ignore the line as it will rotate to 0 which we don't want.
                                        #fileHandler.write(f" - ignored body: {line}")
                                        line = operationFile.readline()
                                        continue
                                    else: # Write our own rotation code based on the provided rotation angle
                                        lineNumber = self._writeLine(fileHandler, "(Rotating between setups)", lineNumber, addLineNumbers, digits)
                                        # Using G53 for absolute machine coordinates for safe retraction
                                        if Settings(Settings.SAFE_Y_RETRACTION):
                                            lineNumber = self._writeLine(fileHandler, "G90 G53 G0 Z-3 Y{yRetraction}".format(yRetraction=Settings(Settings.Y_RETRACTION_COORDINATE)), lineNumber, addLineNumbers, digits)
                                        else:
                                            lineNumber = self._writeLine(fileHandler, "G90 G53 G0 Z-3", lineNumber, addLineNumbers, digits)
                                        lineNumber = self._writeLine(fileHandler, "G90 G54 G0 A{:.3f}".format(rotationAngle), lineNumber, addLineNumbers, digits)

                                        #fileHandler.write(f" - ignored body: {line}")
                                        line = operationFile.readline()
                                        continue

                        lineNumber = self._write(fileHandler, line, lineNumber, addLineNumbers, digits)
                    #else:
                        #fileHandler.write(f" - ignored body: {line}")
                    line = operationFile.readline()
                    row += 1
                    if row >= self._tailStartLine:                            
                        break
            return lineNumber

        raise TypeError("Call GenerateBody(fileHandler) or GenerateBody(folderPath, fileName, fileExtension)")
    #endregion

    def _writeLine(self, fileHandler: TextIO, line: str, lineNumber: int, addLineNumbers: bool, digits: int) -> int:
        """
        Writes the line to the fileHandler and terminates it with a newline (\\n), adding line numbers if needed and returns the new line number
        
        :param self: Description
        :param fileHandler: Description
        :type fileHandler: TextIO
        :param line: Description
        :type line: str
        :param lineNumber: Description
        :type lineNumber: int
        :param addLineNumbers: Description
        :type addLineNumbers: bool
        :param digits: Description
        :type digits: int
        :return: Description
        :rtype: int
        """
        return self._write(fileHandler, line + "\n", lineNumber, addLineNumbers, digits)

    # Writes the line to the fileHandler, adding line numbers if needed and returns the new line number
    def _write(self, fileHandler: TextIO, line: str, lineNumber: int, addLineNumbers: bool, digits: int) -> int:
        """
        Writes the line to the fileHandler, adding line numbers if needed and returns the new line number
        
        :param self: Description
        :param fileHandler: Description
        :type fileHandler: TextIO
        :param line: Description
        :type line: str
        :param lineNumber: Description
        :type lineNumber: int
        :param addLineNumbers: Description
        :type addLineNumbers: bool
        :param digits: Description
        :type digits: int
        :return: Description
        :rtype: int
        """
        # Check if the line is numbered
        match = self._BODY_RE.match(line)
        if match and match.group("N") is not None:
            # If there should be line numbers, replace existing otherwise remove them
            line = re.sub(r"^N[0-9]+", f"N{str(lineNumber).rjust(digits, '0')}" if addLineNumbers else "", line, count=1)
        elif addLineNumbers:
            lineNumber += Settings(Settings.SEQUENCE_INCREMENT)
            line = f"N{str(lineNumber).rjust(digits, '0')} " + line
        fileHandler.write(line)
        return lineNumber

    #region GenerateTail
    # Type signatures for tools (mypy/IDE) hints

    # If GenerateTail is called with a fileHandler it means that the output
    # will only be one file
    @overload
    def GenerateTail(self, fileHandler: TextIO, lineNumber: int, addLineNumbers: bool, digits: int) -> int: ...

    # If GenerateTail is called with folder it means that 
    # multiple files will be generated on lower levels of the hierarchy
    @overload
    def GenerateTail(self, folderPath: Path, lineNumber: int, addLineNumbers: bool, digits: int, fileName: str, fileExtension: str) -> int: ...

    # Runtime implementation of Generate
    def GenerateTail(self, arg, lineNumber: int, addLineNumbers: Optional[bool] = None, digits: Optional[int] = None, fileName: Optional[str] = None, fileExtension: Optional[str] = None) -> int:

        # case 1: given an open file (TextIO) means that everything 
        # should be written to it and not creating a new file
        if isinstance(arg, io.TextIOBase) and fileName is None and fileExtension is None:
            fileHandler: TextIO = arg
            with self._tempFilePath.open("r") as operationFile:
                line = operationFile.readline()
                row = 0
                while len(line) != 0:
                    if row == self._tailStartLine: # Add an extra line marking where this operation tail starts
                        if(self._allowBlankLines):
                            fileHandler.write("\n") # ensure blank line before operation tail
                        lineNumber = self._writeLine(fileHandler, f"({self.name} Tail)", lineNumber, addLineNumbers, digits)
                    if row >= self._tailStartLine:
                        lineNumber = self._write(fileHandler, line, lineNumber, addLineNumbers, digits)
                    line = operationFile.readline()
                    row += 1
            return lineNumber

        raise TypeError("Call GenerateTail(fileHandler) or GenerateTail(folderPath, fileName, fileExtension)")
    #endregion  

    # def Generate(self, outputFile: TextIO):
    #     if not self._tempFilePath.exists():
    #         raise Exception(f"Temporary file '{self._tempFilePath}' does not exist.")

    #     outputFile.write(f"(--- Start of operation: {self.name} ---)\n")
    #     return

    #     fBlankOk = False

    #     # % at start only
    #     line = fileOp.readline()
    #     if line[0] == "%":
    #         if firstOp:
    #             fileHead.write(line)
    #         line = fileOp.readline()

    #     # check for initial comments and tool
    #     # send it to header
    #     while line[0] == "(" or line[0] == "O" or line[0] == "\n":
    #         if line[0] == "\n":
    #             fBlankOk = True
    #         toolComment = regToolComment.search(line)
    #         if toolComment:
    #             toolName = toolComment.group(1)
    #             if toolName not in knownTools:
    #                 knownTools.append(toolName)
    #                 fileHead.write(line)
    #             line = fileOp.readline()
    #             continue # Handle that there might be more than one tool in a setup file (contary to an opFile)

    #         if firstOp:
    #             pos = line.upper().find(opName.upper())
    #             if pos != -1:
    #                 pos += len(opName)
    #                 if numericName:
    #                     fill = "0" * (pos - len(fname) - 1)
    #                 else:
    #                     fill = ""
    #                 line = line[0] + fill + fname + line[pos:]    # correct file name
    #             fileHead.write(line)
    #         line = fileOp.readline()
    #     return fBlankOk, line, knownTools



    #     tail, fBlankOk = PostProcessOperations(docSettings, fileHead, fileBody, fileOp, fname, newSetup, opName, firstOp, regBody, isRotated, wcsRotationAngle, knownTools, fBlankOk)

    #     newSetup = False

    #     if firstOp:
    #         tailGcode = tail
    #         firstOp = False

    #     # Completed all operations, add tail to body file
    #     # Update line numbers if present
    #     if tailGcode:
    #         for code in tailGcode.splitlines(True):
    #             match = regBody.match(code).groupdict()
    #             if match["N"] != None:
    #                 fileBody.write("N" + str(lineNum) + " " + match["line"])
    #                 lineNum += constLineNumInc
    #             else:
    #                 fileBody.write(code)

    #     #
    #     # Copy body to head if not single file output
    #     #
    #     if headerFile is None:
    #         fileBody.close()

    #         fileBody = open(fileBody.name)  # open for reading
    #         # copy in chunks
    #         while True:
    #             block = fileBody.read(10240)
    #             if len(block) == 0:
    #                 break
    #             fileHead.write(block)
    #             block = None    # free memory
    #         fileBody.close()
    #         os.remove(fileBody.name)
    #         fileBody = None
    #         fileHead.close()
    #         fileHead = None

    #     #return None, fBlankOk
