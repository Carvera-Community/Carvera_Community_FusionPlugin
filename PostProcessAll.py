from __future__ import annotations
#Author-Magnus Andersson
#Description-Post process all CAM setups, allowing the user to choose how the output is organized. 
# Derivative work of the PostProcessAll by Tim Paterson

import adsk.core, adsk.fusion, adsk.cam, traceback, shutil, json, os, os.path, time, re, enum, tempfile, logging, math
from typing import List, Final
from pathlib import Path

# Enable debug-level output by setting environment variable POSTPROCESSALL_DEBUG=1
_debug_enabled = True #os.environ.get('POSTPROCESSALL_DEBUG', '0') not in ('0', '', 'False', 'false')
_logger = logging.getLogger('PostProcessAll')
if not _logger.handlers:
    try:
        log_path = os.path.splitext(__file__)[0] + '.log'
        fh = logging.FileHandler(log_path, encoding='utf-8')
        fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
        _logger.addHandler(fh)
    except Exception:
        pass
_logger.setLevel(logging.DEBUG if _debug_enabled else logging.INFO)

def dbg(msg, *args, level='debug'):
    """Write a debug/info/warning/error message to the add-in log file.

    Usage: dbg('something %s', value)
    """
    try:
        if level == 'debug':
            _logger.debug(msg, *args)
        elif level == 'info':
            _logger.info(msg, *args)
        elif level == 'warning':
            _logger.warning(msg, *args)
        else:
            _logger.error(msg, *args)
    except Exception:
        # Best effort only - never crash the add-in for logging failures
        pass

# Version number of settings as saved in documents and settings file
# update this whenever settings content changes
version = 1

# Initial default values of settings
defaultSettings = {
    "version" : version,
    "ncProgram": "",
    "output" : "",
    "sequence" : True,
    "twoDigits" : False,
    "delFiles" : False,
    "delFolder" : False,
    "splitSetup" : False,
    "singleFileOutput": False,
    "rotateAAxis" : False,
    "combineTool" : False,
    "fastZ" : False,
    "toolChange" : "M9 G30",
    "numericName" : False,
    "endCodes" : "M5 M9 M30",
    "onlySelected" : False,
    # Groups are expanded or not
    "groupPersonal" : True,
    "groupPost" : False,
    "groupAdvanced" : False,
    "groupRename" : False,
    # Retry policy
    "initialDelay" : 0.2,
    "postRetries" : 3
}
# Constants
constCmdName = "Post Process All"
constCmdDefId = "BMA_PostProcessAll"
constCAMWorkspaceId = "CAMEnvironment"
constCAMActionsPanelId = "CAMActionPanel"
constPostProcessControlId = "IronPostProcess"
constCAMProductId = "CAMProductType"
constAttrGroup = constCmdDefId
constAttrName = "settings"
constAttrCompressedName = "CompressedName"
constSettingsFileExt = ".settings"
constPostLoopDelay = 0.1
constBodyTmpFile = "gcodeBody"
constOpTmpFile = "8910"   # in case name must be numeric
constRapidZgcode = 'G00 Z{} (Changed from: "{}")\n'
constRapidXYgcode = 'G00 {} (Changed from: "{}")\n'
constFeedZgcode = 'G01 Z{} F{} (Changed from: "{}")\n'
constFeedXYgcode = 'G01 {} F{} (Changed from: "{}")\n'
constFeedXYZgcode = 'G01 {} Z{} F{} (Changed from: "{}")\n'
constAddFeedGcode = " F{} (Feed rate added)\n"
constMotionGcodeSet = {0,1,2,3,33,38,73,76,80,81,82,84,85,86,87,88,89}
constHomeGcodeSet = {28, 30}
constLineNumInc = 5


# Tool tip text
toolTip = (
    "Post process all setups into G-code for your machine.\n\n"
    "The name of the setup is used for the name of the output "
    "file adding the appropriate extension. A colon (':') in the name indicates "
    "the preceding portion is the name of a subfolder. Multiple "
    "colons can be used to nest subfolders. Spaces around colons "
    "are removed.\n\n"
    "Setups within a folder are optionally preceded by a "
    "sequence number. This identifies the order in which the "
    "setups appear. The sequence numbers for each folder begin "
    "with 1."
    )

# Global list to keep all event handlers in scope.
# This is only needed with Python.
handlers = []

# Global settingsMgr object
settingsMgr = None



#
# Helpers
#

def GetNcProgram(cam, settings):
    for program in cam.ncPrograms:
        if program.name == settings["ncProgram"]:
            return program
    return cam.ncPrograms.item(0)

def RenameSetups(settings, setups, find, replace, isRegex):
    try:
        app = adsk.core.Application.get()
        doc = app.activeDocument
        cam = adsk.cam.CAM.cast(doc.products.itemByProductType(constCAMProductId))
        #setups = GetSetups(cam, settings, setups)
        
        for setup in setups:
            if isRegex:
                newName = re.sub(find, replace, setup.name)
            else:
                if find == "":
                    # special case, prepend
                    newName = replace + setup.name
                else:
                    newName = setup.name.replace(find, replace)

            if setup.name != newName:
                setup.name = newName

        # Save settings in document attributes
        settingsMgr.SaveSettings(doc.attributes, settings)

    except:
        pass

def CompressFileName(file):
    # normalize whacks 
    base = os.path.expanduser("~").replace("\\", "/")
    newFile = file.replace("\\", "/").removeprefix(base)
    if len(file) != len(newFile) and newFile[0] == "/":
        file = "~" + newFile
    return file

def ExpandFileName(file):
    return os.path.expanduser(file).replace("\\", "/")


def CountOutputFolderFiles(folder, limit, fileExt):
    cntFiles = 0
    cntNcFiles = 0
    for path, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith(fileExt):
                cntNcFiles += 1
            else:
                cntFiles += 1
        if cntFiles > limit:
            return "many files that are not G-code"
        if cntNcFiles > limit * 1.5:
            return "many more G-code files than are produced by this design"
    return None

# Event handler for the commandCreated event.
class CommandEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        dbg("PostProcessAll CommandEventHandler __init__")
        super().__init__()

    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            cmd = eventArgs.command

            Program()

            # Get the NCProgram
            programs = Program.cam.ncPrograms
            if programs.count == 0:
                ncInput = programs.createInput()
                ncInput.displayName = Program.name
                program = programs.add(ncInput)
                program.postConfiguration = program.postConfiguration
                outputFolder = Program.settings["output"]
                program.attributes.add(constAttrGroup, constAttrCompressedName, outputFolder)
                Program.SetOutputFolder(ExpandFileName(outputFolder))
                program.parameters.itemByName("nc_program_createInBrowser").value.value = True
            elif programs.count == 1:
                program = programs.item(0)
            else:
                haveProgram = False
                for program in programs:
                    if program.name == Program.settings["ncProgram"]:
                        haveProgram = True
                        break
                if not haveProgram:
                    program = programs.item(0)              
            Program.settings["ncProgram"] = program.name

            # Connect to the execute event.
            onExecute = CommandExecuteHandler(Program.settings, Setups.selected)
            cmd.execute.add(onExecute)
            handlers.append(onExecute)

            # Add inputs that will appear in a dialog
            inputs = cmd.commandInputs

            # text box as a label for NC Program
            input = inputs.addTextBoxCommandInput("ncProgramLabel", 
                                                   "", 
                                                   "NC Program:",
                                                   1,
                                                   True)
            input.isFullWidth = True
            label = input

            input = inputs.addDropDownCommandInput("ncProgram", 
                                                   "NC Program",
                                                   adsk.core.DropDownStyles.TextListDropDownStyle)
            for listItem in programs:
                input.listItems.add(listItem.name, listItem.name == program.name)
            #input.isFullWidth = True
            input.tooltip = "NC Program to Use"
            input.tooltipDescription = (
                "Post processing will use the settings from the selected NC Program."
            )
            label.tooltip = input.tooltip
            label.tooltipDescription = input.tooltipDescription

            # check box to use only selected setups
            input = inputs.addBoolValueInput("onlySelected", 
                                             "Only selected setups", 
                                             True, 
                                             "", 
                                             Program.settings["onlySelected"])
            input.tooltip = "Only Process Selected Setups"
            input.tooltipDescription = (
                "Only setups selected in the browser will be processed. Note "
                "that a selected setup will be highlighted, not simply activated. "
                "Selecting individual operations within a setup has no effect."
            )
            input.isEnabled = Program.Setups.hasSelection

            # "Personal Use" version
            # check box to split up setup into individual operations
            inputGroup = inputs.addGroupCommandInput("groupPersonal", "Personal Use")

            # checkbox to add rotation of the A-axis between setups
            input = inputGroup.children.addBoolValueInput("rotateAAxis",
                                                          "Rotate A-Axis Between Setups",
                                                          True,
                                                          "",
                                                          Program.settings["rotateAAxis"])
            input.isEnabled = Program.settings["singleFileOutput"] # enable only if merging all outputs to one file
            input.tooltip = "Rotate A-Axis Between Setups if required."
            input.tooltipDescription = (
                "If you have an A-axis and you have setups that is using a WCS with a "
                "different Z-direction that rotates around the X-axis this will rotate "
                "the A-axis between the setups to align the Z-axis with the spindle "
                "so that the Z-axis of the WCS always points up."
                "Please note that you need to make sure that the X-axis of all WCS "
                "is aligned the same way.")

            # check box to combine operation that use the same tool
            input = inputGroup.children.addBoolValueInput("combineTool",
                                                          "Combine operations using same tool",
                                                          True,
                                                          "",
                                                          Program.settings["combineTool"])
            input.isEnabled = Program.settings["splitSetup"] # enable only if using individual operations
            input.tooltip = "Combine Consecutive Operations That Use the Same Tool"
            input.tooltipDescription = (
                "If consecutive operations use the same tool, have Fusion generate "
                "their output together. This can optimize G-code for some routers. "
                "However, it will cause the logic that restores rapid moves to also "
                "treat it as one operation, which can have negative effects if the "
                "feed heights for the operations are different.")

            # text box as a label for tool change command
            input = inputGroup.children.addTextBoxCommandInput("toolLabel", 
                                                               "", 
                                                               "G-code for tool change:",
                                                               1,
                                                               True)
            input.isFullWidth = True
            label = input

            # enter G-code for tool change
            input = inputGroup.children.addStringValueInput("toolChange", "", Program.settings["toolChange"])
            input.isEnabled = Program.settings["splitSetup"] # enable only if using individual operations
            input.isFullWidth = True
            input.tooltip = "G-code to Precede Tool Change"
            input.tooltipDescription = (
                "Allows inserting a line of code before tool changes. For example, "
                "you might want M5 (spindle stop), M9 (coolant stop), and/or G28 or G30 "
                "(return to home). The code will be placed on the line before the "
                "tool change. You can get mulitple lines by separating them with "
                "a colon (:)."
                "<p>If you want a line number, just put a dummy line number in front. "
                "If you use the colon to get multiple lines, only put the dummy line "
                "number on the first line. For example, <b>N10 M9:G30</b> will give "
                "you two lines, both with properly sequenced line numbers.</p>"
            )
            label.tooltip = input.tooltip
            label.tooltipDescription = input.tooltipDescription
           
            # text box as a label for operation end commands
            input = inputGroup.children.addTextBoxCommandInput("endLabel", 
                                                               "", 
                                                               "G-codes that mark ending sequence:",
                                                               1,
                                                               True)
            input.isFullWidth = True
            label = input

            # enter G-codes for end of operation
            input = inputGroup.children.addStringValueInput("endCodes", "", Program.settings["endCodes"])
            input.isEnabled = Program.settings["splitSetup"] # enable only if using individual operations
            input.isFullWidth = True
            input.tooltip = "G-codes That Mark the Ending Sequence"
            input.tooltipDescription = (
                "To combine operations generated individually, the ending sequence "
                "(which should only appear once) must be found. This entry is the "
                "list of G-codes that start this ending sequence. For example, M30 "
                "(end program) would normally be here, but it may not be the first "
                "G-code of the ending sequence. M5 (spindle stop), M9 (coolant "
                "stop) and G28/G30 (move home) are also candidates, but you should "
                "look at the code from your post processor to determine what "
                "will work in your case. Any one of the G-codes you enter here "
                "will mark the start of ending sequence."
            )
            label.tooltip = input.tooltip
            label.tooltipDescription = input.tooltipDescription
           
            # check box to enable restoring rapid moves
            input = inputGroup.children.addBoolValueInput("fastZ",
                                                          "Restore rapid moves",
                                                          True,
                                                          "",
                                                          Program.settings["fastZ"])
            input.isEnabled = Program.settings["splitSetup"] # enable only if using individual operations
            input.tooltip = "Restore Rapid Moves (Experimental)"
            input.tooltipDescription = (
                "Replace appropriate moves at feed rate with rapid (G0) moves. "
                "In Fusion for Personal Use, moves that could be rapid are "
                "now limited to the current feed rate. When this option is selected, "
                "the G-code will be analyzed to find moves at or above the feed "
                "height and replace them with rapid moves."
                "<p><b>WARNING!<b> This option should be used with caution. "
                "Review the G-code to verify it is correct. Comments have been "
                "added to indicate the changes.")
           
            inputGroup.isExpanded = Program.settings["groupPersonal"]

            # Output options
            # Output path
            inputGroup = inputs.addGroupCommandInput("groupOutput", "Output options")
            input = inputGroup.children.addTextBoxCommandInput("outputlabel", 
                                                   "", 
                                                   "Output folder:",
                                                   1,
                                                   True)
            input.isFullWidth = True
            label = input

            input = inputGroup.children.addStringValueInput("outputFolder", "", Program.GetOutputFolder())
            input.isFullWidth = True
            input.tooltip = "Path for output files"
            input.tooltipDescription = (
                "This is the folder that the output will be written to in the end."
            )
            label.tooltip = input.tooltip
            label.tooltipDescription = input.tooltipDescription

            # check box to delete entire output folder
            input = inputGroup.children.addBoolValueInput("delFolder", 
                                             "Delete output folder", 
                                             True, 
                                             "", 
                                             Program.settings["delFolder"] and Program.settings["delFiles"])
            input.isEnabled = Program.settings["delFiles"] # enable only if delete existing files
            input.tooltip = "Delete Entire Output Folder First"
            input.tooltipDescription = (
                "Delete the entire output folder before post processing. This "
                "deletes all files and subfolders regardless of whether or not "
                "new G-code files are written to a particular folder."
                "<p><b>WARNING!</b> Be absolutely sure the output folder is set "
                "correctly before selecting this option. Run the command once "
                "before setting this option and verify the results are in the "
                "correct folder. An incorrect setting of the output folder with "
                "this option selected could result in unintentionally wiping out "
                "a vast number of files.</p>")

            # File option
            input = inputGroup.children.addDropDownCommandInput("operationsGrouping", 
                                                   "Operations grouping",
                                                   adsk.core.DropDownStyles.TextListDropDownStyle)
            input.listItems.add("Single file", False)
            input.listItems.add("Group on setup", False)
            input.listItems.add("Group on setup and tool", False)
            input.listItems.add("Do not group", True)
            #input.isFullWidth = True
            input.tooltip = "Operations grouping"
            input.tooltipDescription = (
                "<p>Choose how operations are grouped into output files."
                "<p><i><u>Single file</u></i>: All operations are combined into one single output file. "
                "Only possible if all setups share the same Work Coordinate System (WCS) <i>or</i> "
                "if the 'Rotate A-Axis Between Setups' option is selected, all WCS have the same origo + X-axis orientation and "
                "the machine has an A-axis. Note that the rotation will be performed aground WCS origo."
                "<p><i><u>Group on setup</u></i>: Operations are grouped into one file per setup.<br>"
                "Naming convention: &lt;sequence&gt;_&lt;setup name&gt;.&lt;extension&gt;"
                "<p><i><u>Group on setup and tool</u></i>: Operations are grouped into one file per setup setup and tool."
                "<p><i><u>Do not group</u></i>: Each operation is output to a separate file."
            )
            label.tooltip = input.tooltip
            label.tooltipDescription = input.tooltipDescription

            # check box to flatten the file structure
            input = inputGroup.children.addBoolValueInput("flatFilestructure",
                                                          "Flat file structure",
                                                          True,
                                                          "",
                                                          False)
            input.isEnabled = Program.settings["splitSetup"] # enable only if using individual operations
            input.tooltip = "Flatten the file structure"
            input.tooltipDescription = (
                "When outputting to multiple files the default behaviour is to "
                "put everything in a folder hirarchy to avoid the risk of creating "
                "files with the same filename. "
                "<p>Enable this option if you rather would like the output to be "
                "files directly in the output folder with unique file names based "
                "on setup/tool/operation name.")


            # check box to prepend sequence numbers
            input = inputGroup.children.addBoolValueInput("sequence", 
                                             "Prepend sequence number", 
                                             True, 
                                             "", 
                                             Program.settings["sequence"])
            input.tooltip = "Add Sequence Numbers to Name"
            input.tooltipDescription = (
                "Begin each file name with a sequence number. The numbering "
                "represents the order that the setups appear in the browser tree. "
                "Each folder has its own sequence numbers starting with 1.")

            # check box to select 2-digit sequence numbers
            input = inputGroup.children.addBoolValueInput("twoDigits", 
                                             "Use 2-digit numbers", 
                                             True, 
                                             "", 
                                             Program.settings["twoDigits"])
            input.isEnabled = Program.settings["sequence"] # enable only if using sequence numbers
            input.tooltip = "Use 2-Digit Sequence Numbers"
            input.tooltipDescription = (
                "Sequence numbers 0 - 9 will have a leading zero added, becoming"
                '"01" to "09". This could be useful for formatting or sorting.')

            # check box to delete existing files
            input = inputGroup.children.addBoolValueInput("delFiles", 
                                             "Delete existing files", 
                                             True, 
                                             "", 
                                             Program.settings["delFiles"])
            input.tooltip = "Delete Existing Files in Each Folder"
            input.tooltipDescription = (
                "Delete all files in each output folder before post processing. "
                "This will help prevent accumulation of G-code files which are "
                "no longer used."
                "<p>For example, you could decide to add sequence numbers after "
                "already post processing without them. If this option is not "
                "checked, you will have two of each file, a newer one with a "
                "sequence number and older one without. With this option checked, "
                "all previous files will be deleted so only current results will "
                "be present.</p>"
                "<p>This option will only delete the files in folders in which new "
                "G-code files are being written. If you change the name of a "
                "folder, for example, it will not be deleted.</p>")

            # Rename
            inputGroup = inputs.addGroupCommandInput("groupRename", "Rename Setups")

            # check box to use regular expressions
            input = inputGroup.children.addBoolValueInput("regex",
                                                          "Use Python regular expressions",
                                                          True,
                                                          "",
                                                          False)
            input.tooltip = "Search With Regular Expressions"
            input.tooltipDescription = (
                "Treat the search string as a Python regular expression (regex). "
                "This is extremely flexible but also very technical. Refer to "
                "Python documentation for details."
                "<p>One example is to put $ in the search box. This special "
                "symbol searches for the end of the setup name. Then the replacement "
                "string will be appended to the existing name."
            )

            # text box as a label for search field
            input = inputGroup.children.addTextBoxCommandInput("searchLabel", 
                                                               "", 
                                                               "Search for this string:",
                                                               1,
                                                               True)
            input.isFullWidth = True
            label = input

            # Find
            input = inputGroup.children.addStringValueInput("findString", "")
            input.isFullWidth = True
            input.tooltip = "String to find in setup name"
            input.tooltipDescription = (
                "Replace all occurences of this string with the replacement string. "
                "If this is left blank, the replacement string will be prepended to "
                "each setup name."
            )
            label.tooltip = input.tooltip
            label.tooltipDescription = input.tooltipDescription

            # text box as a label for replace field
            input = inputGroup.children.addTextBoxCommandInput("replaceLabel", 
                                                               "", 
                                                               "Replace with this string:",
                                                               1,
                                                               True)
            input.isFullWidth = True
            label = input

            # Replace
            input = inputGroup.children.addStringValueInput("replaceString", "")
            input.isFullWidth = True
            input.tooltip = "String to use as replacement"
            input.tooltipDescription = (
                "Replace all occurences of the Find string with this string."
            )
            label.tooltip = input.tooltip
            label.tooltipDescription = input.tooltipDescription

            # button to execute search & replace
            input = inputGroup.children.addBoolValueInput("replace", "Search and replace", False)
            input.resourceFolder = "resources/Rename"
            input.tooltip = "Execute search and replace"
            input.tooltipDescription = (
                "Search for all strings matching the Find box and replace them "
                "with the string in the Replace box.")
            inputGroup.isExpanded = Program.settings["groupRename"]

            # Advanced -- retry settings
            inputGroup = inputs.addGroupCommandInput("groupAdvanced", "Advanced")
            # Time delay
            input = inputGroup.children.addFloatSpinnerCommandInput("initialDelay", 
                "Initial time allowance", "s", 0.1, 1.0, 0.1, Program.settings["initialDelay"])
            input.tooltip = "Initial Time to Post Process an Operation"
            input.tooltipDescription = (
                "Initial delay to wait for post processor. Doubled for each retry.")
            # Retry count
            input = inputGroup.children.addIntegerSpinnerCommandInput("postRetries", 
                "Number of retries", 1, 9, 1, Program.settings["postRetries"])
            input.tooltip = "Number of Retries"
            input.tooltipDescription = (
                "Retries if post processing failed. Time delay is doubled each retry.")
            inputGroup.isExpanded = Program.settings["groupAdvanced"]
            
            # post processor
            inputGroup = inputs.addGroupCommandInput("groupPost", "Post Processor")
            inputGroup.isExpanded = Program.settings["groupPost"]

            # Numeric name required?
            input = inputGroup.children.addBoolValueInput("numericName",
                                                          "Name must be numeric",
                                                          True,
                                                          "",
                                                          Program.settings["numericName"])
            input.tooltip = "Output File Name Must Be Numeric"
            input.tooltipDescription = (
                "The name of the setup will not be used in the file name, "
                "only sequence numbers. The option to prepend sequence numbers "
                "will have no effect.")

            # button to save default settings
            input = inputs.addBoolValueInput("save", "Save as default", False)
            input.resourceFolder = "resources/Save"
            input.tooltip = "Save These Settings as System Default"
            input.tooltipDescription = (
                "Save these settings to use as the default for each new design.")

            # text box for error messages
            input = inputs.addTextBoxCommandInput("error", "", "", 3, True)
            input.isFullWidth = True
            input.isVisible = False

            # Connect to the inputChanged event.
            onInputChanged = CommandInputChangedHandler(Program.settings, Setups.selected)
            cmd.inputChanged.add(onInputChanged)
            handlers.append(onInputChanged)

            # Connect to the validateInputs event.
            onValidateInputs = CommandValidateInputsHandler()
            cmd.validateInputs.add(onValidateInputs)
            handlers.append(onValidateInputs)
        except:
            ui = Program.app.userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# Event handler for the inputChanged event.
class CommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self, docSettings, selectedSetups):
        dbg("PostProcessAll CommandInputChangedHandler __init__")
        self.docSettings = docSettings
        self.selectedSetups = selectedSetups
        super().__init__()

    def notify(self, args):
        app = adsk.core.Application.get()
        ui  = app.userInterface
        try:
            eventArgs = adsk.core.InputChangedEventArgs.cast(args)
            cmd = eventArgs.input.parentCommand
            inputs = eventArgs.inputs

            doc = app.activeDocument
            cam = adsk.cam.CAM.cast(doc.products.itemByProductType(constCAMProductId))

            # See if button clicked
            input = eventArgs.input
            if input.id == "save":
                settingsMgr.SaveDefault(self.docSettings)

            elif input.id == "replace":
                cmd.doExecute(False)    # do it in execute handler for Undo
                return

            elif input.id in self.docSettings:
                if input.objectType == adsk.core.GroupCommandInput.classType():
                    self.docSettings[input.id] = input.isExpanded
                elif input.objectType == adsk.core.DropDownCommandInput.classType():
                    self.docSettings[input.id] = input.selectedItem.name
                else:
                    self.docSettings[input.id] = input.value

            # Enable twoDigits only if sequence is true
            if input.id == "sequence":
                inputs.itemById("twoDigits").isEnabled = input.value

            # Enable delFolder only if delFiles is true
            if input.id == "delFiles":
                item = inputs.itemById("delFolder")
                item.value = input.value and item.value
                item.isEnabled = input.value

            # Options for splitSetup
            if input.id == "splitSetup":
                inputs.itemById("singleFileOutput").isEnabled = input.value
                inputs.itemById("combineTool").isEnabled = input.value
                inputs.itemById("toolChange").isEnabled = input.value
                inputs.itemById("toolLabel").isEnabled = input.value
                inputs.itemById("endCodes").isEnabled = input.value
                inputs.itemById("endLabel").isEnabled = input.value
                inputs.itemById("fastZ").isEnabled = input.value
            
            # Options for singleFileOutput
            if input.id == "singleFileOutput":
                inputs.itemById("rotateAAxis").isEnabled = input.value

        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Event handler for the validateInputs event.
class CommandValidateInputsHandler(adsk.core.ValidateInputsEventHandler):
    def __init__(self):
        dbg("PostProcessAll CommandValidateInputsHandler __init__")
        super().__init__()

    def notify(self, args):
        app = adsk.core.Application.get()
        ui  = app.userInterface

        # No validation currently performed. Skeleton code retained.
        try:
            eventArgs = adsk.core.ValidateInputsEventArgs.cast(args)
            inputs = eventArgs.firingEvent.sender.commandInputs

        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Event handler for the execute event.
class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self, docSettings, selectedSetups):
        dbg("PostProcessAll CommandExecuteHandler __init__")
        self.docSettings = docSettings
        self.selectedSetups = selectedSetups
        super().__init__()

    def notify(self, args):
        eventArgs = adsk.core.CommandEventArgs.cast(args)
        cmd = eventArgs.command
        inputs = cmd.commandInputs

        # Code to react to the event.
        button = inputs.itemById("replace")
        if button.value:
            RenameSetups(self.docSettings, 
                        self.selectedSetups, 
                        inputs.itemById("findString").value, 
                        inputs.itemById("replaceString").value,
                        inputs.itemById("regex").value)
            button.value = False
        else:
            Program.Process() # First go through the setups and generate the separate files to find all the information needed
            Program.Generate() # then create the actual output from those files and the information collected.


class Program:
    def __init__(self):
        Program.name: Final = "PostProcessAll NC Program"

        Program._app = adsk.core.Application.get()
        Program._ui = Program._app.userInterface
        Program._doc = Program._app.activeDocument
        Program._program = None
        Program._outputFolder = None

        Program.cam = adsk.cam.CAM.cast(Program._doc.products.itemByProductType(constCAMProductId))
        Program.settings = settingsMgr.GetSettings(Program._doc.attributes)
        Program.Setups = Setups()

        Program.attributes = None
        Program.parameters = None
        Program.fileExtension = ""

    @classproperty
    def name(self):
        return Program.GetParameter("nc_program_name")

    @staticmethod
    def Set(program):
        #Program._program = next((program for program in Program.cam.ncPrograms if program.name == Program.settings["ncProgram"]), None)
        #if Program._program is None: # Grab the first program if none was selected (is it even possible..?)
        #    Program._program = Program.cam.ncPrograms.item(0)
        Program._program = program
        Program.attributes = Program._program.attributes
        Program.parameters = Program._program.parameters
        Program.fileExtension = Program.GetParameter("nc_program_nc_extension")

    @staticmethod
    def Process():
        oldOutputFolder = Program.GetOutputFolder()

        if not Program.GetSetting("delFiles"):
            Program.SetSetting("delFolder", False) # Only remove folders if files will be removed too

        if Program.GetSetting("delFolder"):
            fileExt = Program.GetParameter("nc_program_nc_extension")
            strMsg = CountOutputFolderFiles(Program._outputFolder, len(Program.Setups.Count()), fileExt)
            if strMsg:
                Program.SetSetting("delFolder", False)
                strMsg = (
                    "The output folder contains {}. "
                    "It will not be deleted. You may wish to make sure you selected "
                    "the correct folder. If you want the folder deleted, you must "
                    "do it manually."
                    ).format(strMsg)
                res = Program._ui.messageBox(strMsg, 
                                    constCmdName,
                                    adsk.core.MessageBoxButtonTypes.OKCancelButtonType,
                                    adsk.core.MessageBoxIconTypes.WarningIconType)
                if res == adsk.core.DialogResults.DialogCancel:
                    return  # abort!

        if Program.GetSetting("delFolder"):
            try:
                shutil.rmtree(Program._outputFolder, True)
            except:
                pass #ignore errors

        # Make sure that the root folder exists as defined in the NC Program parameters
        Program.CreateAndSetOutputFolder()

        # Start showing progress here

        Program.Setups.Process()

        # Restore the output folder in the NC Program parameters
        Program.SetOutputFolder(oldOutputFolder)

    @staticmethod
    def Generate():
        if True:
            Program.Setups.SetOutputFileName(Program.name)
        Program.Setups.Generate()
        pass

    @staticmethod
    def DisableOpenInEditor():
        Program.SetParameter("nc_program_openInEditor", False)

    @staticmethod
    def GetParameter(name):
        return Program.parameters.itemByName(name).value.value
    
    @staticmethod
    def SetParameter(name, value):
        Program.parameters.itemByName(name).value.value = value

    @staticmethod
    def GetAttribute(group, name):
        attr = Program.attributes.itemByName(group, name)
        if attr is not None:
            return attr.value
        return None
    
    @staticmethod
    def SetAttribute(group, name, value):
        Program.attributes.add(group, name, value)

    @staticmethod
    def PostProcess(operations):
        Program._program.operations = operations
        return Program._program.postProcess(adsk.cam.NCProgramPostProcessOptions.create())

    @staticmethod
    def GetSetting(setting):
        return Program.settings[setting]
    
    @staticmethod
    def SetSetting(setting, value):
        Program.settings[setting] = value

    @staticmethod
    def SetOutputFolder(folder):
        Program.SetParameter("nc_program_output_folder", folder)
        result = Program.GetOutputFolder()
        if result != folder and folder[0:2] == "\\\\":
            Program.SetParameter("nc_program_output_folder", "\\\\" + folder)    # double up leading "\"
        return None

    @staticmethod
    def GetOutputFolder():
        return Program.GetParameter("nc_program_output_folder")

    @staticmethod
    def CreateAndSetOutputFolder():
        outputFolder = Program.GetOutputFolder().replace("\\", "/")
        if outputFolder[0:2] == "//": # Preserve network share
            outputFolder = "\\\\" + outputFolder[2:]
        Program._outputFolder = outputFolder
        try:
            Path(Program._outputFolder).mkdir(exist_ok=True)
        except Exception as exc:
            # see if we can map it to folder with compressed user
            compressedName = Program.GetAttribute(constAttrGroup, constAttrCompressedName)
            if compressedName[0] == "~" and compressedName[1:] == Program._outputFolder[-(len(compressedName) - 1):]:
                # yes, it matches
                Program._outputFolder = ExpandFileName(compressedName)

        compressedName = CompressFileName(Program._outputFolder)
        Program.SetAttribute(constAttrGroup, constAttrCompressedName, compressedName)
        Program.SetSetting("output", compressedName)

        # Save settings in document attributes
        settingsMgr.SaveSettings(Program.attributes, Program.settings)

    @staticmethod
    def CheckAndGenerateToolpath(setup):
        if not Program.cam.checkToolpath(setup):
            genStat = Program.cam.generateToolpath(setup)
            while not genStat.isGenerationCompleted:
                time.sleep(.1)

class Setups:
    def __init__(self):
        self._outputFileName = None
        self._setups: List[Setup] = []
        self._setups = [Setup(setup) for setup in Program.cam.setups] # Collect all setups

    def SetOutputFileName(self, fileName):
        self._outputFileName = fileName

    def Process(self):
        seqDict = {}  # keep track of sequence numbers per folder

        for setup in self._setups:

            # Build up folder path if there are subfolders
            nameList = setup.name.split(':')    # folder separator
            setupFolder = Program._outputFolder
            cnt = len(nameList) - 1
            i = 0
            while i < cnt:
                setupFolder += "/" + nameList[i].strip()
                i += 1
        
            # keep a separate sequence number for each folder
            if setupFolder in seqDict:
                seqDict[setupFolder] += 1
                # skip if we're not actually including this setup
                if setup not in self.selected:
                    continue
            else:
                # first file for this folder
                seqDict[setupFolder] = 1
                # skip if we're not actually including this setup
                if setup not in self.selected:
                    continue

                if (Program.GetSetting("delFiles")):
                    # delete all the files in the folder
                    try:
                        for entry in os.scandir(setupFolder):
                            if entry.is_file():
                                try:
                                    os.remove(entry.path)
                                except:
                                    pass #ignore errors
                    except:
                        pass #ignore errors

            outputFileName = nameList[i].strip() # setup name without folder parts
            # If enabled prepend sequence number to file name 
            if Program.GetSetting("sequence") or Program.GetSetting("numericName"):
                seq = seqDict[setupFolder]
                seqStr = str(seq)
                if Program.GetSetting("twoDigits") and seq < 10:
                    seqStr = "0" + seqStr
                if Program.GetSetting("numericName"):
                    outputFileName = seqStr
                else:
                    outputFileName = seqStr + ' ' + outputFileName

            setup.outputFilePath = setupFolder + "/" + outputFileName + Program.fileExtension

            # post the file (per Setup)
            setup.Process()

    def Generate(self):
        for setup in self.selected:
            if self._outputFileName is not None:
                setup.SetOutputFileName(f"{self._outputFileName}_{setup.name}")
            setup.Generate()

    def RenameAll(self, find, replace, isRegex):
        for setup in self._setups:
            setup.Rename(find, replace, isRegex)

    @property
    def selected(self):
        return [setup for setup in self._setups if (not Program.GetSetting("onlySelected") or setup.isSelected) and not setup.isSuppressed]
    @property
    def hasSelection(self):
        return any(setup.isSelected and not setup.isSuppressed for setup in self._setups)

    @property
    def Count(self):
        return len(self._setups)

class Setup:
    def __init__(self, setup):
        self._setup = setup
        self._outputFilename = None
        # Only process operations if necessary
        self._operations = None if \
                self.isSuppressed \
                or not Program.GetSetting("splitSetup") \
                or (Program.GetSetting("onlySelected") \
                    and not self.isSelected) \
            else Operations(list(operation for operation in self._setup.allOperations))
        self.outputFilePath = ""

    @property
    def isSuppressed(self):
        return self._setup is None or self._setup.isSuppressed
    
    @property
    def isSelected(self):
        return self._setup is None or self._setup.isSelected

    @property
    def name(self):
        return self._setup.name

    def Rename(self, find, replace, isRegex):
        if isRegex:
            newName = re.sub(find, replace, self._setup.name)
        else:
            if find == "":
                # special case, prepend
                newName = replace + self._setup.name
            else:
                newName = self._setup.name.replace(find, replace)

        if self._setup.name != newName:
            self._setup.name = newName
    
    def Process(self):
        if self.isSuppressed or (Program.GetSetting("onlySelected") and not self.isSelected):
            return # Don't process this setup.
        
        path = Path(self.outputFilePath)
        #try:
        setupFolder = path.parent
        setupFolder.mkdir(parents=True, exist_ok=True)
        #except Exception as exc:
        #    return "Unable to create output file '" + self.outputFilePath + "'. Make sure the setup name is valid as a file name.", None
    
        Program.CheckAndGenerateToolpath(self._setup)

        # set up NCProgram parameters
        opName = path.stem
        operationsFolder = str(setupFolder)
        
        #if Program.GetSetting("splitSetup"):
        #    opName = constOpTmpFile
        #    opFolder = tempfile.gettempdir()    # e.g., C:\Users\Tim\AppData\Local\Temp
        #    opFolder = opFolder.replace("\\", "/")

        Program.DisableOpenInEditor()

        # Do it all at once?
        if not Program.GetSetting("splitSetup"):
            Program.SetOutputFolder(str(setupFolder))

            Program.SetParameter("nc_program_filename", opName)
            Program.SetParameter("nc_program_name", path.stem)
            try:
                if not Program.PostProcess([self._setup]):
                    raise Exception(f"Setup {self.name} post processing failed.")
                time.sleep(constPostLoopDelay) # files missing sometimes unless we slow down (??)
                return
            except Exception as exc:
                retVal += ": " + str(exc)
                return retVal, None
        #
        # Split setup into individual operations
        # It will only be set if the setup is selected 
        # or if all setups should be processed
        # as long as the setup isn't suppressed
        #
        if self._operations is None:
            return  # nothing to do
        
        operationsFolder = setupFolder / self.name
        operationsFolder.mkdir(parents=True, exist_ok=True)

        self._operations.SetOutputFolder(str(operationsFolder))
        self._operations.Process()

    def SetOutputFileName(self, fileName):
        self._outputFileName = fileName

    def Generate(self):
        if self._outputFileName is not None:
            self._operations.SetOutputFileName(f"{self._outputFileName}")
        self._operations.Generate()

class Operations:
    def __init__(self, operations):
        self._outputFileName = None
        self._operations = list[Operation]()

        i = 0
        operation = None
        while i < len(operations):
            # Look ahead for operations without a toolpath. This can happen
            # with a manual operation. Group it with current operation.
            # Or if first, group it with subsequent ones.
            # Also optionally group together operations with the same tool number

            operation = Operation()
            operation.Append(operations[i], operations[i].hasToolpath) # add first operation
            i += 1
            while i < len(operations):
                # Append to current group if:
                # - operation has no toolpath, or
                # - current group has no tool yet (we haven't encountered a toolpath), or
                # - we're combining tools and this op uses the same tool as the group
                # otherwise finish current group and start a new one
                if (not operations[i].hasToolpath) \
                    or (not operation.hasTool) \
                    or (Program.GetSetting("combineTool") \
                        and Operations.GetToolNumber(operations[i]) == operation.toolId):
                    operation.Append(operations[i], operations[i].hasToolpath)
                    i += 1
                else:
                    # different tool (or not combining) -> finish current group
                    self._operations.append(operation)
                    break
        if operation is not None: # append final group
            self._operations.append(operation)
                
    def SetOutputFolder(self, folder):
        self._outputFolder = folder

    @staticmethod
    def GetToolNumber(operation):
        return operation.tool.parameters.itemByName("tool_number").value.value

    def Process(self):
        for operation in self._operations:
            operation.SetOutputFolder(self._outputFolder)
            operation.Process()

    def SetOutputFileName(self, fileName):
        self._outputFileName = fileName

    def Generate(self):
        for operation in self._operations:
            if self._outputFileName is not None:
                operation.SetOutputFileName(f"{self._outputFileName}_{operation.name}")
            operation.Generate()

class Operation:
    _BODY_RE: Final = re.compile(r""
        r"(?P<N>N[0-9]+ *)?" # line number
        r"(?P<line>"         # line w/o number
        r"(M(?P<M>[0-9]+) *)?" # M-code
        r"(G(?P<G>[0-9]+) *)?" # G-code
        r"(T(?P<T>[0-9]+))?" # Tool
        r".+)",              # to end of line
        re.IGNORECASE | re.DOTALL)
    
    _PARSE_LINE_RE: Final = re.compile(r""
            r"(G(?P<G>[0-9]+(\.[0-9]*)?)[^XYZF]*)?"
            r"(?P<XY>((X-?[0-9]+(\.[0-9]*)?)[^XYZF]*)?"
            r"((Y-?[0-9]+(\.[0-9]*)?)[^XYZF]*)?)"
            r"(Z(?P<Z>-?[0-9]+(\.[0-9]*)?)[^XYZF]*)?"
            r"(F(?P<F>-?[0-9]+(\.[0-9]*)?)[^XYZF]*)?",
            re.IGNORECASE)
    
    _GCODES_RE: Final = re.compile(r"G([0-9]+(?:\.[0-9]*)?)")

    _TOOL_COMMENT_REG: Final = re.compile(r"\((T[0-9])+\s")

    _COMMENT_REG: Final = re.compile(r"^(?:\s*)\((.*)\)(?:\s*)$")


    def __init__(self):
        self._outputFileName = None
        self._operationsList = []

    def Append(self, operation, hasTool):
        self._operationsList.append(operation)
        if hasTool:
            self._operationWithTool = operation

    @property
    def toolId(self):
        return Operations.GetToolNumber(self._operationWithTool) \
            if self._operationWithTool is not None \
                and self._operationWithTool.hasToolpath \
            else None

    @property
    def hasTool(self):
        return self._operationWithTool is not None and self._operationWithTool.hasToolpath

    @property
    def name(self):
        return self._operationWithTool.name if self._operationWithTool is not None else "NoToolOperation"

    def SetOutputFolder(self, folder):
        self._outputFilePath = folder

    def Process(self):
        path = Path(self._outputFilePath) / (self.name + Program.fileExtension)

        if(path.exists()):
            path.unlink(missing_ok=True)

        Program.SetOutputFolder(str(path.parent))

        Program.SetParameter("nc_program_filename", path.stem)
        Program.SetParameter("nc_program_name", self.name)
        try:
            if not Program.PostProcess(self._operationsList):
                raise Exception(f"Operation {self.name} post processing failed.")
            time.sleep(constPostLoopDelay) # files missing sometimes unless we slow down (??)
        except Exception as exc:
            retVal += ": " + str(exc)
            return retVal, None
        

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

        operationFile = path.open("r")
        # Locate header rows
        line = operationFile.readline()
        inHeader = False
        self._toolCommentLine = -1
        lineNumber = -1
        processBody = False
        processHeader = True
        allowBlankLines = False
        while len(line) != 0:
            lineNumber += 1

            if not allowBlankLines and line[0] == "\n":
                allowBlankLines = True

            if processHeader:
                # Some checks to verify that we're in the header.
                if not inHeader:
                    if line[0] == "%" or line[0] == "(" or line[0] == "O" or line[0] == "\n":
                        inHeader = True
                if inHeader:
                    toolComment = self._TOOL_COMMENT_REG.search(line)
                    if toolComment: # We have found the tool comment line
                        self._toolCommentLine = lineNumber
                    if self._toolCommentLine != -1 and line.strip() == f"({self.name})":
                        # found body start
                        self._bodyStartLine = lineNumber
                        processHeader = False
                        processBody = True
                line = operationFile.readline()
                continue

            # Locate body rows
            if processBody:
                match = self._BODY_RE.match(line)
                if match:
                    if match.group("T") is not None:
                        # found body start
                        self._bodyStartLine = lineNumber
                    if match.group("M") is not None:
                        mCode = int(match.group("M"))
                        if f"M{mCode}" in Program.GetSetting("endCodes"):
                            # found tail start
                            self._tailStartLine = lineNumber
                line = operationFile.readline()


        # Identify tail rows
        operationFile.close()

        return

    def SetOutputFileName(self, fileName):
        self._outputFileName = fileName

    def Generate(self):
        p = Path(self._outputFilePath)
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
        filePath = p / (self._outputFileName + Program.fileExtension)
        filePath.touch(exist_ok=True)
        return

        fBlankOk = False

        # % at start only
        line = fileOp.readline()
        if line[0] == "%":
            if firstOp:
                fileHead.write(line)
            line = fileOp.readline()

        # check for initial comments and tool
        # send it to header
        while line[0] == "(" or line[0] == "O" or line[0] == "\n":
            if line[0] == "\n":
                fBlankOk = True
            toolComment = regToolComment.search(line)
            if toolComment:
                toolName = toolComment.group(1)
                if toolName not in knownTools:
                    knownTools.append(toolName)
                    fileHead.write(line)
                line = fileOp.readline()
                continue # Handle that there might be more than one tool in a setup file (contary to an opFile)

            if firstOp:
                pos = line.upper().find(opName.upper())
                if pos != -1:
                    pos += len(opName)
                    if numericName:
                        fill = "0" * (pos - len(fname) - 1)
                    else:
                        fill = ""
                    line = line[0] + fill + fname + line[pos:]    # correct file name
                fileHead.write(line)
            line = fileOp.readline()
        return fBlankOk, line, knownTools



        tail, fBlankOk = PostProcessOperations(docSettings, fileHead, fileBody, fileOp, fname, newSetup, opName, firstOp, regBody, isRotated, wcsRotationAngle, knownTools, fBlankOk)

        newSetup = False

        if firstOp:
            tailGcode = tail
            firstOp = False

        # Completed all operations, add tail to body file
        # Update line numbers if present
        if tailGcode:
            for code in tailGcode.splitlines(True):
                match = regBody.match(code).groupdict()
                if match["N"] != None:
                    fileBody.write("N" + str(lineNum) + " " + match["line"])
                    lineNum += constLineNumInc
                else:
                    fileBody.write(code)

        #
        # Copy body to head if not single file output
        #
        if headerFile is None:
            fileBody.close()

            fileBody = open(fileBody.name)  # open for reading
            # copy in chunks
            while True:
                block = fileBody.read(10240)
                if len(block) == 0:
                    break
                fileHead.write(block)
                block = None    # free memory
            fileBody.close()
            os.remove(fileBody.name)
            fileBody = None
            fileHead.close()
            fileHead = None

        #return None, fBlankOk
