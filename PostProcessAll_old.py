#Author-Tim Paterson
#Description-Post process all CAM setups, using the setup name as the output file name.

import adsk.core, adsk.fusion, adsk.cam, traceback, shutil, json, os, os.path, time, re, pathlib, enum, tempfile, logging, math

# Simple file-based logger for development/debugging.
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
version = 12

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
constCmdDefId = "PatersonTech_PostProcessAll"
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
constNcProgramName = "PostProcessAll NC Program"

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

def run(context):
    global settingsMgr
    ui = None
    try:
        settingsMgr = SettingsManager()
        app = adsk.core.Application.get()
        ui  = app.userInterface
        InitAddIn()

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        # Clean up the UI.
        cmdDef = ui.commandDefinitions.itemById(constCmdDefId)
        if cmdDef:
            cmdDef.deleteMe()
            
        addinsPanel = ui.allToolbarPanels.itemById(constCAMActionsPanelId)
        cmdControl = addinsPanel.controls.itemById(constCmdDefId)
        if cmdControl:
            cmdControl.deleteMe()
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))	


class SettingsManager:
    def __init__(self):
        self.default = None
        self.path = None
        self.fMustSave = False
        self.inputs = None

    def GetSettings(self, docAttr):
        docSettings = None
        attr = docAttr.itemByName(constAttrGroup, constAttrName)
        if attr:
            try:
                docSettings = json.loads(attr.value)
                if docSettings["version"] == version:
                    return docSettings
            except Exception:
                pass
            
        # Document does not have valid settings, get defaults
        if not self.default:
            # Haven't read the settings file yet
            file = None
            try:
                file = open(self.GetPath())
                self.default = json.load(file)
                # never allow delFiles or delFolder to default to True
                self.default["delFiles"] = False
                self.default["delFolder"] = False
                if self.default["version"] != version:
                    self.UpdateSettings(defaultSettings, self.default)
            except Exception:
                self.default = dict(defaultSettings)
                self.fMustSave = True
            finally:
                if file:
                    file.close
        
        if not docSettings:
            docSettings = dict(self.default)
        else:
            self.UpdateSettings(self.default, docSettings)
        return docSettings

    def SaveDefault(self, docSettings):
        self.fMustSave = False
        self.default = dict(docSettings)
        # never allow delFiles or delFolder to default to True
        self.default["delFiles"] = False
        self.default["delFolder"] = False
        try:
            strSettings = json.dumps(docSettings)
            file = open(self.GetPath(), "w")
            file.write(strSettings)
            file.close
        except Exception:
            pass

    def SaveSettings(self, docAttr, docSettings):
        if self.fMustSave:
            self.SaveDefault(docSettings)
        docAttr.add(constAttrGroup, constAttrName, json.dumps(docSettings))
            
    def UpdateSettings(self, src, dst):
        if "homeEndsOp" in dst:
            if dst["homeEndsOp"] and not ("endCodes" in dst):
                dst["endCodes"] = "M5 M9 M30 G28 G30"
            del dst["homeEndsOp"]
        for item in src:
            if not (item in dst):
                dst[item] = src[item]
        dst["version"] = src["version"]

    def GetPath(self):
        if not self.path:
            pos = __file__.rfind(".")
            if pos == -1:
                pos = len(__file__)
            self.path = __file__[0:pos] + constSettingsFileExt
        return self.path


def InitAddIn():
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        # Create a button command definition.
        cmdDefs = ui.commandDefinitions
        cmdDef = cmdDefs.addButtonDefinition(constCmdDefId, constCmdName, toolTip, "resources/Command")
        
        # Connect to the commandCreated event.
        commandEventHandler = CommandEventHandler()
        cmdDef.commandCreated.add(commandEventHandler)
        handlers.append(commandEventHandler)
        
        # Get the Actions panel in the Manufacture workspace.
        workSpace = ui.workspaces.itemById(constCAMWorkspaceId)
        addInsPanel = workSpace.toolbarPanels.itemById(constCAMActionsPanelId)
        
        # Add the button right after the Post Process command.
        cmdControl = addInsPanel.controls.addCommand(cmdDef, constPostProcessControlId, False)
        cmdControl.isPromotedByDefault = True
        cmdControl.isPromoted = True

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


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


def ExpandFileName(file):
    return os.path.expanduser(file).replace("\\", "/")


def CompressFileName(file):
    # normalize whacks 
    base = os.path.expanduser("~").replace("\\", "/")
    newFile = file.replace("\\", "/").removeprefix(base)
    if len(file) != len(newFile) and newFile[0] == "/":
        file = "~" + newFile
    return file


def AssignOutputFolder(parameters, folder):
    parameters.itemByName("nc_program_output_folder").value.value = folder
    result = parameters.itemByName("nc_program_output_folder").value.value
    if result != folder and folder[0:2] == "\\\\":
        parameters.itemByName("nc_program_output_folder").value.value = "\\\\" + folder    # double up leading "\"
    return None


def GetSetups(cam, settings, setups):
    if len(setups) == 0 or not settings["onlySelected"]:
        setups = []
        # move all setups into a list
        for setup in cam.setups:
            setups.append(setup)
    return setups


def GetNcProgram(cam, settings):
    for program in cam.ncPrograms:
        if program.name == settings["ncProgram"]:
            return program
    return cam.ncPrograms.item(0)


def RenameSetups(settings, setups, find, replace, isRegex):
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        doc = app.activeDocument
        cam = adsk.cam.CAM.cast(doc.products.itemByProductType(constCAMProductId))
        setups = GetSetups(cam, settings, setups)
        
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


# Event handler for the commandCreated event.
class CommandEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            cmd = eventArgs.command

            # Get document attributes that will set initial values
            app = adsk.core.Application.get()
            cam = adsk.cam.CAM.cast(app.activeDocument.products.itemByProductType(constCAMProductId))
            docSettings  = settingsMgr.GetSettings(app.activeDocument.attributes)

            # See if we're doing only selected setups
            selectedSetups = []
            for setup in cam.setups:
                if setup.isSelected:
                    selectedSetups.append(setup)

            # Get the NCProgram
            programs = cam.ncPrograms
            if programs.count == 0:
                ncInput = programs.createInput()
                ncInput.displayName = constNcProgramName
                program = programs.add(ncInput)
                program.postConfiguration = program.postConfiguration
                outputFolder = docSettings["output"]
                program.attributes.add(constAttrGroup, constAttrCompressedName, outputFolder)
                AssignOutputFolder(program.parameters, ExpandFileName(outputFolder))
                program.parameters.itemByName("nc_program_createInBrowser").value.value = True
            elif programs.count == 1:
                program = programs.item(0)
            else:
                haveProgram = False
                for program in programs:
                    if program.name == docSettings["ncProgram"]:
                        haveProgram = True
                        break
                if not haveProgram:
                    program = programs.item(0)              
            docSettings["ncProgram"] = program.name

            # Connect to the execute event.
            onExecute = CommandExecuteHandler(docSettings, selectedSetups)
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
                                             docSettings["onlySelected"])
            input.tooltip = "Only Process Selected Setups"
            input.tooltipDescription = (
                "Only setups selected in the browser will be processed. Note "
                "that a selected setup will be highlighted, not simply activated. "
                "Selecting individual operations within a setup has no effect."
            )
            input.isEnabled = len(selectedSetups) != 0

            # check box to delete existing files
            input = inputs.addBoolValueInput("delFiles", 
                                             "Delete existing files", 
                                             True, 
                                             "", 
                                             docSettings["delFiles"])
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

            # check box to delete entire output folder
            input = inputs.addBoolValueInput("delFolder", 
                                             "Delete output folder", 
                                             True, 
                                             "", 
                                             docSettings["delFolder"] and docSettings["delFiles"])
            input.isEnabled = docSettings["delFiles"] # enable only if delete existing files
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

            # check box to prepend sequence numbers
            input = inputs.addBoolValueInput("sequence", 
                                             "Prepend sequence number", 
                                             True, 
                                             "", 
                                             docSettings["sequence"])
            input.tooltip = "Add Sequence Numbers to Name"
            input.tooltipDescription = (
                "Begin each file name with a sequence number. The numbering "
                "represents the order that the setups appear in the browser tree. "
                "Each folder has its own sequence numbers starting with 1.")

            # check box to select 2-digit sequence numbers
            input = inputs.addBoolValueInput("twoDigits", 
                                             "Use 2-digit numbers", 
                                             True, 
                                             "", 
                                             docSettings["twoDigits"])
            input.isEnabled = docSettings["sequence"] # enable only if using sequence numbers
            input.tooltip = "Use 2-Digit Sequence Numbers"
            input.tooltipDescription = (
                "Sequence numbers 0 - 9 will have a leading zero added, becoming"
                '"01" to "09". This could be useful for formatting or sorting.')

            # "Personal Use" version
            # check box to split up setup into individual operations
            inputGroup = inputs.addGroupCommandInput("groupPersonal", "Personal Use")
            input = inputGroup.children.addBoolValueInput("splitSetup",
                                                          "Use individual operations",
                                                          True,
                                                          "",
                                                          docSettings["splitSetup"])
            input.tooltip = "Split Setup Into Individual Operations"
            input.tooltipDescription = (
                "Generate output for each operation individually. This is usually "
                "REQUIRED when using Fusion for Personal Use, because tool "
                "changes are not allowed. The individual operations will be "
                "grouped back together into the same file, eliminating this "
                "limitation. You will get an error if there is a tool change "
                "in a setup and this options is not selected.")

            # checkbox to merge the resulting setup files
            input = inputGroup.children.addBoolValueInput("singleFileOutput",
                                                          "Create single file",
                                                          True,
                                                          "",
                                                          docSettings["singleFileOutput"])
            input.tooltip = "Create single file"
            input.tooltipDescription = (
                "Create one single file for all setups instead of one file per setup. "
                "This is useful if you want to run all the setups in sequence without "
                "having to load multiple files into your CNC controller."
                "Please note that if the setups have different WCS it is required "
                "that they all face the same direction (Z-axis points up)")

            # checkbox to add rotation of the A-axis between setups
            input = inputGroup.children.addBoolValueInput("rotateAAxis",
                                                          "Rotate A-Axis Between Setups",
                                                          True,
                                                          "",
                                                          docSettings["rotateAAxis"])
            input.isEnabled = docSettings["singleFileOutput"] # enable only if merging all outputs to one file
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
                                                          docSettings["combineTool"])
            input.isEnabled = docSettings["splitSetup"] # enable only if using individual operations
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
            input = inputGroup.children.addStringValueInput("toolChange", "", docSettings["toolChange"])
            input.isEnabled = docSettings["splitSetup"] # enable only if using individual operations
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
            input = inputGroup.children.addStringValueInput("endCodes", "", docSettings["endCodes"])
            input.isEnabled = docSettings["splitSetup"] # enable only if using individual operations
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
                                                          docSettings["fastZ"])
            input.isEnabled = docSettings["splitSetup"] # enable only if using individual operations
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
           
            inputGroup.isExpanded = docSettings["groupPersonal"]

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
            inputGroup.isExpanded = docSettings["groupRename"]

            # Advanced -- retry settings
            inputGroup = inputs.addGroupCommandInput("groupAdvanced", "Advanced")
            # Time delay
            input = inputGroup.children.addFloatSpinnerCommandInput("initialDelay", 
                "Initial time allowance", "s", 0.1, 1.0, 0.1, docSettings["initialDelay"])
            input.tooltip = "Initial Time to Post Process an Operation"
            input.tooltipDescription = (
                "Initial delay to wait for post processor. Doubled for each retry.")
            # Retry count
            input = inputGroup.children.addIntegerSpinnerCommandInput("postRetries", 
                "Number of retries", 1, 9, 1, docSettings["postRetries"])
            input.tooltip = "Number of Retries"
            input.tooltipDescription = (
                "Retries if post processing failed. Time delay is doubled each retry.")
            inputGroup.isExpanded = docSettings["groupAdvanced"]
            
            # post processor
            inputGroup = inputs.addGroupCommandInput("groupPost", "Post Processor")
            inputGroup.isExpanded = docSettings["groupPost"]

            # Numeric name required?
            input = inputGroup.children.addBoolValueInput("numericName",
                                                          "Name must be numeric",
                                                          True,
                                                          "",
                                                          docSettings["numericName"])
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
            onInputChanged = CommandInputChangedHandler(docSettings, selectedSetups)
            cmd.inputChanged.add(onInputChanged)
            handlers.append(onInputChanged)

            # Connect to the validateInputs event.
            onValidateInputs = CommandValidateInputsHandler()
            cmd.validateInputs.add(onValidateInputs)
            handlers.append(onValidateInputs)
        except:
            ui = app.userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# Event handler for the inputChanged event.
class CommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self, docSettings, selectedSetups):
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
            PerformPostProcess(self.docSettings, self.selectedSetups)

# Main function to perform post processing
def PerformPostProcess(docSettings, setups):

    dbg(" -- PerformPostProcess -- ")

    ui = None
    progress = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        doc = app.activeDocument
        cam = adsk.cam.CAM.cast(doc.products.itemByProductType(constCAMProductId))

        cntFiles = 0
        cntSkipped = 0
        lstSkipped = ""

        program = GetNcProgram(cam, docSettings)
        parameters = program.parameters
        setups = GetSetups(cam, docSettings, setups)

        # normalize output folder for this user
        # "\" is converted to "/"
        outputFolder = parameters.itemByName("nc_program_output_folder").value.value.replace("\\", "/")
        
        # keep leading "\\" for file share
        if outputFolder[0:2] == "//":
            outputFolder = "\\\\" + outputFolder[2:]
        try:
            pathlib.Path(outputFolder).mkdir(exist_ok=True)
        except Exception as exc:
            # see if we can map it to folder with compressed user
            compressedName = program.attributes.itemByName(constAttrGroup, constAttrCompressedName).value
            if compressedName[0] == "~" and compressedName[1:] == outputFolder[-(len(compressedName) - 1):]:
                # yes, it matches
                outputFolder = ExpandFileName(compressedName)

        compressedName = CompressFileName(outputFolder)
        program.attributes.add(constAttrGroup, constAttrCompressedName, compressedName)
        docSettings["output"] = compressedName

        # Save settings in document attributes
        settingsMgr.SaveSettings(doc.attributes, docSettings)

        if len(setups) != 0 and cam.allOperations.count != 0:
            # make sure we're not going to delete too much
            if not docSettings["delFiles"]:
                docSettings["delFolder"] = False

            if docSettings["delFolder"]:
                fileExt = parameters.itemByName("nc_program_nc_extension").value.value
                strMsg = CountOutputFolderFiles(outputFolder, len(setups), fileExt)
                if strMsg:
                    docSettings["delFolder"] = False
                    strMsg = (
                        "The output folder contains {}. "
                        "It will not be deleted. You may wish to make sure you selected "
                        "the correct folder. If you want the folder deleted, you must "
                        "do it manually."
                        ).format(strMsg)
                    res = ui.messageBox(strMsg, 
                                        constCmdName,
                                        adsk.core.MessageBoxButtonTypes.OKCancelButtonType,
                                        adsk.core.MessageBoxIconTypes.WarningIconType)
                    if res == adsk.core.DialogResults.DialogCancel:
                        return  # abort!

            if docSettings["delFolder"]:
                try:
                    shutil.rmtree(outputFolder, True)
                except:
                    pass #ignore errors

            progress = ui.createProgressDialog()
            progress.isCancelButtonShown = True
            progressMsg = "{} files written to " + outputFolder
            progress.show("Post Processing...", "", 0, len(setups))
            progress.progressValue = 1 # try to get it to display
            progress.progressValue = 0

            cntSetups = 0
            seqDict = dict()


            wcsRotationAngle = 0
            isRotated = False
            previousNormal = adsk.core.Vector3D.create(0,1,0)  # Default orientation, Z is up
            fNames = list()

            headerFile = None
            bodyFile = None
            fileExt = parameters.itemByName("nc_program_nc_extension").value.value

            if docSettings["singleFileOutput"]:
                # Prepare header and body files
                singleFileName = doc.name + fileExt
                headerPath = outputFolder + "/" + "header_" + singleFileName
                bodyPath = outputFolder + "/" + "body_" + singleFileName
                headerFile = open(headerPath, 'w')
                bodyFile = open(bodyPath, 'w')
                knownTools = []
                fBlankOk = False

            # We pass through all setups even if only some are selected
            # so numbering scheme doesn't change.
            for setup in cam.setups:
#################
                if progress.wasCancelled:
                    dbg("Cancelled.")
                    break

                # Just count the setups that we're not interested in
                if setup.isSuppressed or setup.allOperations.count == 0:
                    cntSetups += 1
                    progress.message = progressMsg.format(cntFiles)
                    progress.progressValue = cntSetups
                    continue

                # Calculate the rotation of the A-axis
                if docSettings["singleFileOutput"] and docSettings["rotateAAxis"]:
                    dbg(f"rotateAAxis: {docSettings["rotateAAxis"]}")
                    exception = None
                    normal = None
                    directionX = directionY = directionZ = None
                    wcs_orientation_axisX =  wcs_orientation_axisY =  wcs_orientation_axisZ = None

                    wcs_orientation_mode = adsk.cam.ChoiceParameterValue.cast(setup.parameters.itemByName("wcs_orientation_mode").value).value
                    # Get if any axis should be flipped.
                    wcs_orientation_flipX = adsk.cam.BooleanParameterValue.cast(setup.parameters.itemByName("wcs_orientation_flipX").value).value
                    wcs_orientation_flipY = adsk.cam.BooleanParameterValue.cast(setup.parameters.itemByName("wcs_orientation_flipY").value).value
                    wcs_orientation_flipZ = adsk.cam.BooleanParameterValue.cast(setup.parameters.itemByName("wcs_orientation_flipZ").value).value

                    dbg('Setup name: %s', setup.name)
                    dbg('Orientation mode: %s', wcs_orientation_mode)

                    match wcs_orientation_mode:
                        case 'modelOrientation':
                            # Have to get the model orientation to get the orientation of the WCS
                            exception = NotImplementedError("modelOrientation not implemented")
                        
                        case 'axesZX' | 'axesXZ':
                            wcs_orientation_axisZ = setup.parameters.itemByName("wcs_orientation_axisZ") # CAMParameter
                            face = adsk.fusion.BRepFace.cast(wcs_orientation_axisZ.value.value[0])

                            if face: # If the z-axis is defined by a face, get normal from face and we're done.
                                dbg(f"({wcs_orientation_mode}) Z defined by face")
                                centroid = adsk.core.Point3D.cast(face.centroid)
                                evaluator = face.evaluator
                                success, normal = evaluator.getNormalAtPoint(centroid)
                                if not success:
                                    raise Exception(f"{wcs_orientation_mode} Z axis face normal not found")
                                
                                directionZ = normal.copy()

                                # Choose a stable reference vector (world X); if nearly parallel, use world Y
                                ref = adsk.core.Vector3D.create(1, 0, 0)
                                if abs(directionZ.dotProduct(ref)) > 0.999:  # nearly parallel
                                    ref = adsk.core.Vector3D.create(0, 1, 0)

                                # Compute X = Z × (ref × Z) which lies in the plane orthogonal to Z
                                directionX = directionZ.crossProduct(ref.crossProduct(directionZ))    # directionX = Z × (ref × Z)

                                if not directionX or directionX.length == 0:
                                    raise Exception(f"{wcs_orientation_mode} Failed to compute directionX from face normal")

                                directionX.normalize()

                                # Compute Y to satisfy right-hand rule X × Y = Z
                                directionY = directionX.crossProduct(directionZ)
                                directionY.normalize()
                            else:
                                edgeZ = adsk.fusion.BRepEdge.cast(wcs_orientation_axisZ.value.value[0])

                                if not edgeZ:
                                    raise Exception(f"{wcs_orientation_mode} Z axis not defined by edge or face")

                                dbg(f"({wcs_orientation_mode}) Z defined by edge")

                                wcs_orientation_axisX = setup.parameters.itemByName("wcs_orientation_axisX") # CAMParameter
                                edgeX = adsk.fusion.BRepEdge.cast(wcs_orientation_axisX.value.value[0])

                                if not edgeX:
                                    raise Exception(f"{wcs_orientation_mode} X axis not defined by edge")

                                directionZ = edgeZ.startVertex.geometry.vectorTo(edgeZ.endVertex.geometry)
                                directionX = edgeX.startVertex.geometry.vectorTo(edgeX.endVertex.geometry)

                                if wcs_orientation_flipZ:
                                    directionZ.scaleBy(-1)
                                if wcs_orientation_flipX:
                                    directionX.scaleBy(-1)
                                if directionZ.length == 0 or directionX.length == 0:
                                    raise Exception(f"{wcs_orientation_mode} Zero-length direction vector for normal calculation")

                                # Compute Y to satisfy right-hand rule X × Y = Z
                                directionY = directionX.crossProduct(directionZ)
                                directionY.normalize()

                                normal = adsk.core.Vector3D.crossProduct(directionX, directionZ)

                        case 'axesZY':
                            wcs_orientation_axisZ = setup.parameters.itemByName("wcs_orientation_axisZ") # CAMParameter
                            face = adsk.fusion.BRepFace.cast(wcs_orientation_axisZ.value.value[0])

                            if face: # If the z-axis is defined by a face, get normal from face and we're done.
                                dbg(f"({wcs_orientation_mode}) Z defined by face")
                                centroid = adsk.core.Point3D.cast(face.centroid)
                                evaluator = face.evaluator
                                success, normal = evaluator.getNormalAtPoint(centroid)
                                if not success:
                                    raise Exception(f"{wcs_orientation_mode} Z axis face normal not found")
                                directionZ = normal.copy()

                                # Choose a stable reference vector (world X); if nearly parallel, use world Y
                                ref = adsk.core.Vector3D.create(1, 0, 0)
                                if abs(directionZ.dotProduct(ref)) > 0.999:  # nearly parallel
                                    ref = adsk.core.Vector3D.create(0, 1, 0)

                                # Compute X = Z × (ref × Z) which lies in the plane orthogonal to Z
                                directionX = directionZ.crossProduct(ref.crossProduct(directionZ))    # directionX = Z × (ref × Z)

                                if not directionX or directionX.length == 0:
                                    raise Exception(f"{wcs_orientation_mode} Failed to compute directionX from face normal")

                                directionX.normalize()

                                # Compute Y to satisfy right-hand rule X × Y = Z
                                directionY = directionX.crossProduct(directionZ)
                                directionY.normalize()
                            else:
                                edgeZ = adsk.fusion.BRepEdge.cast(wcs_orientation_axisZ.value.value[0])
                                
                                if not edgeZ:
                                    raise Exception(f"{wcs_orientation_mode} Z axis not defined by edge or face")
                                
                                dbg(f"({wcs_orientation_mode}) Z defined by edge")
                                
                                wcs_orientation_axisY = setup.parameters.itemByName("wcs_orientation_axisY") # CAMParameter
                                edgeY = adsk.fusion.BRepEdge.cast(wcs_orientation_axisY.value.value[0])
                                
                                if not edgeY:
                                    raise Exception(f"{wcs_orientation_mode} Y axis not defined by edge")
                                
                                directionZ = edgeZ.startVertex.geometry.vectorTo(edgeZ.endVertex.geometry)
                                directionY = edgeY.startVertex.geometry.vectorTo(edgeY.endVertex.geometry)
                                
                                if wcs_orientation_flipZ:
                                    directionZ.scaleBy(-1)
                                if wcs_orientation_flipY:
                                    directionY.scaleBy(-1)
                                
                                if directionZ.length == 0 or directionY.length == 0:
                                    raise Exception(f"{wcs_orientation_mode} Zero-length direction vector for normal calculation")
                                
                                normal = adsk.core.Vector3D.crossProduct(directionY, directionZ)
                                
                                directionX = directionY.crossProduct(directionZ)

                        case 'axesXY':
                            wcs_orientation_axisX = setup.parameters.itemByName("wcs_orientation_axisX") # CAMParameter
                            edgeX = adsk.fusion.BRepEdge.cast(wcs_orientation_axisX.value.value[0])
                            
                            if not edgeX:
                                raise Exception(f"{wcs_orientation_mode} X axis not defined by edge or face")
                            
                            dbg(f"({wcs_orientation_mode}) X defined by edge")
                            
                            wcs_orientation_axisY = setup.parameters.itemByName("wcs_orientation_axisY") # CAMParameter
                            edgeY = adsk.fusion.BRepEdge.cast(wcs_orientation_axisY.value.value[0])
                            if not edgeY:
                                raise Exception(f"{wcs_orientation_mode} Y axis not defined by edge")
                            directionX = edgeX.startVertex.geometry.vectorTo(edgeX.endVertex.geometry)
                            directionY = edgeY.startVertex.geometry.vectorTo(edgeY.endVertex.geometry)
                            if wcs_orientation_flipX:
                                directionX.scaleBy(-1)
                            if wcs_orientation_flipY:
                                directionY.scaleBy(-1)
                            if directionX.length == 0 or directionY.length == 0:
                                raise Exception(f"{wcs_orientation_mode} Zero-length direction vector for normal calculation")
                            normal = adsk.core.Vector3D.crossProduct(directionX, directionY)

                        case 'coordinateSystem':
                            exception = NotImplementedError("coordinateSystem not implemented")
                        
                        case 'fromArrange':
                            exception = NotImplementedError("fromArrange not implemented")
                        
                        case _:
                            dbg(f"({wcs_orientation_mode})Unknown wcs_orientation_mode: ", wcs_orientation_mode)
                            exception = NotImplementedError("Unknown wcs_orientation_mode: " + wcs_orientation_mode)

                    if not normal or normal.length == 0:
                        raise Exception(f"{wcs_orientation_mode} Failed to calculate normal vector")    
                    normal.normalize()

                    if exception is not None: # Alright, things went bad. Let's dump the WCS variables and skidaddle out of here!
                        dbg("Processing setup: " + setup.name)

                        for param in [p for p in setup.parameters if p.name in [
                            'wcs_orientation_mode',
                            'wcs_orientation_axisZ',
                            'wcs_orientation_flipZ',
                            #'wcs_orientation_axesZX_unselected_default',
                            #'wcs_orientation_axesZY_unselected_default',
                            #'wcs_orientation_axesXY_unselected_default',
                            #'wcs_orientation_axesXZ_unselected_default',
                            'wcs_orientation_cSys',
                            'wcs_orientation_axisX',
                            'wcs_orientation_flipX',
                            'wcs_orientation_axisY',
                            'wcs_orientation_flipY',
                            'wcs_origin_turning',
                            'wcs_origin_mode',
                            'wcs_origin_point',
                            'wcs_model_point',
                            'wcs_origin_boxPoint',
                            'wcs_stock_point']]:

                                output = list()
                                output.append(f'  Parameter: {param.fullTitle} ({param.name}), type: {param.value.objectType}')
                                match param.value.objectType:
                                    case 'adsk::cam::ChoiceParameterValue':
                                        choice = adsk.cam.ChoiceParameterValue.cast(param.value)
                                        choiceValue = "'" + choice.value + "'" # I assume it can be an evaluated value?
                                        found, choiceTexts, choiceValues = choice.getChoices()
                                        if found:
                                            if choiceValue in choiceValues:
                                                output.append(f'    selected: {choiceTexts[choiceValues.index(choiceValue)]}, {choiceValue}')
                                            else:
                                                output.append(f'    selected: {choiceValue}')
                                            output.append(f'    options: {choiceTexts} ({choiceValues})')
                                        else:
                                            output.append(f'    selected: {choiceValue}')
                                    case 'adsk::cam::BooleanParameterValue':
                                        boolean = adsk.cam.BooleanParameterValue.cast(param.value)
                                        output.append(f'    value: {boolean.value}')
                                    case 'adsk::cam::CadObjectParameterValue':
                                        parameterValue = adsk.cam.CadObjectParameterValue.cast(param.value)
                                        output.append(f'    cad object, type: {parameterValue.value}')
                                        value = parameterValue.value
                                        if hasattr(value, 'size'):
                                            if value.size() == 0:
                                                output = list() # Empty value, ignore it.
                                            else:
                                                value = value[0]
                                                point = adsk.core.Point3D.cast(value)
                                                if point:
                                                    output.append(f'    cad point: x={point.x} y={point.y} z={point.z}')
                                                else: 
                                                    vector = adsk.core.Vector3D.cast(value)
                                                    if vector:
                                                        output.append(f'    cad vector: x={vector.x} y={vector.y} z={vector.z}')
                                                    else:
                                                        edge = adsk.fusion.BRepEdge.cast(value)
                                                        if edge:
                                                            output.append(f'    cad edge: {edge.objectType}')
                                                        else:
                                                            face = adsk.fusion.BRepFace.cast(value)
                                                            if face:
                                                                output.append(f'    cad face: {face.objectType}')
                                                            else:
                                                                output.append(f'    cad object: {str(value)}')
                                    case _:
                                        output.append(f'Unknown type: {param.value.objectType}')
                                if output:
                                    for line in output:
                                        dbg(line)

                        raise exception
                    
                    dbg("New Normal: x=%f y=%f z=%f", normal.x, normal.y, normal.z)

                    if cntSetups != 0:
                        # Calculate rotation from previous setup if needed
                        dbg('Calculating A-axis rotation from [%f, %f, %f] to [%f, %f, %f]', previousNormal.x, previousNormal.y, previousNormal.z, normal.x, normal.y, normal.z)

                        deg_unsigned = previousNormal.angleTo(normal) * 180.0 / math.pi # Get the absolute angle in degrees

                        directionX.normalize()
                        projection = directionX.dotProduct(previousNormal.crossProduct(normal))   # >0 => rotation follows right-hand rule

                        tolerance = 1e-9
                        # Sign is inverted as the rotation of the A axis is opposite to the rotation of the tool
                        sign = -1.0 if projection > tolerance else (1.0 if projection < -tolerance else 0.0)
                        deg = deg_unsigned * sign

                        wcsRotationAngle = wcsRotationAngle + deg
                        isRotated = deg_unsigned != 0

                        while wcsRotationAngle > 360:
                            wcsRotationAngle -= 360
                        while wcsRotationAngle < -360:
                            wcsRotationAngle += 360

                        dbg('  Absolute rotation angle: %f degrees', wcsRotationAngle)

                    previousNormal = normal

#################
                nameList = setup.name.split(':')    # folder separator
                setupFolder = outputFolder
                cnt = len(nameList) - 1
                i = 0
                while i < cnt:
                    setupFolder += "/" + nameList[i].strip()
                    i += 1
            
                # keep a separate sequence number for each folder
                if setupFolder in seqDict:
                    seqDict[setupFolder] += 1
                    # skip if we're not actually including this setup
                    if setup not in setups:
                        continue
                else:
                    # first file for this folder
                    seqDict[setupFolder] = 1
                    # skip if we're not actually including this setup
                    if setup not in setups:
                        continue

                    if (docSettings["delFiles"]):
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

                # prepend sequence number if enabled
                fname = nameList[i].strip()
                if docSettings["sequence"] or docSettings["numericName"]:
                    seq = seqDict[setupFolder]
                    seqStr = str(seq)
                    if docSettings["twoDigits"] and seq < 10:
                        seqStr = "0" + seqStr
                    if docSettings["numericName"]:
                        fname = seqStr
                    else:
                        fname = seqStr + ' ' + fname

                # post the file
                status, fBlankOk = PostProcessSetup(program, fname, setup, setupFolder, docSettings, wcsRotationAngle, isRotated, headerFile, bodyFile, knownTools, fBlankOk)
                if status == None:
                    cntFiles += 1
                else:
                    cntSkipped += 1
                    lstSkipped += "\nFailed on setup " + setup.name + ": " + status
                        
                cntSetups += 1
                progress.message = progressMsg.format(cntFiles)
                progress.progressValue = cntSetups

                dbg(f"Known tools: {knownTools}")

            dbg(f"Posted setups: {len(fNames)} files: {fNames}")

            if headerFile is not None and bodyFile is not None:
                headerFile.close()
                bodyFile.close()

                # Combine header and body into single file
                singleFileName = doc.name + fileExt
                singlePath = outputFolder + "/" + singleFileName
                with open(singlePath, 'w') as singleFile:
                    with open(headerPath, 'r') as headerFile:
                        shutil.copyfileobj(headerFile, singleFile)
                    with open(bodyPath, 'r') as bodyFile:
                        shutil.copyfileobj(bodyFile, singleFile)

                # Remove temporary header and body files
                os.remove(headerPath)
                os.remove(bodyPath)

                cntFiles += 1  # Count the single combined file

            progress.hide()
            # restore program output folder
            AssignOutputFolder(parameters, outputFolder)

        # done with setups, report results
        if cntSkipped != 0:
            ui.messageBox("{} files were written. {} Setups were skipped due to error:{}".format(cntFiles, cntSkipped, lstSkipped), 
                constCmdName, 
                adsk.core.MessageBoxButtonTypes.OKButtonType,
                adsk.core.MessageBoxIconTypes.WarningIconType)
            
        elif cntFiles == 0:
            ui.messageBox('No CAM operations posted', 
                constCmdName, 
                adsk.core.MessageBoxButtonTypes.OKButtonType,
                adsk.core.MessageBoxIconTypes.WarningIconType)

    except:
        if progress:
            progress.hide()
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# Post process a single setup
# If the headerFile and bodyFile is not None then they will be used to write the gcode to rather than individual files per setup.
def PostProcessSetup(program, fname, setup, setupFolder, docSettings, wcsRotationAngle, isRotated, headerFile, bodyFile, knownTools, fBlankOk):
    ui = None
    fileHead = headerFile if bodyFile is not None else None
    fileBody = bodyFile if fileHead is not None else None
    fileOp = None
    retVal = "Fusion reported an exception"

    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        doc = app.activeDocument
        cam = adsk.cam.CAM.cast(doc.products.itemByProductType(constCAMProductId))
        parameters = program.parameters

        fileExt = parameters.itemByName("nc_program_nc_extension").value.value

        if headerFile == None: # Use a local header file to create one file per setup rather than one large file
            # Verify file name is valid by creating it now
            path = setupFolder + "/" + fname + fileExt
            try:
                pathlib.Path(setupFolder).mkdir(parents=True, exist_ok=True)
                fileHead = open(path, "w")
            except Exception as exc:
                return "Unable to create output file '" + path + "'. Make sure the setup name is valid as a file name.", None
        
        # Make sure toolpaths are valid
        if not cam.checkToolpath(setup):
            genStat = cam.generateToolpath(setup)
            while not genStat.isGenerationCompleted:
                time.sleep(.1)

        # set up NCProgram parameters
        opName = fname
        opFolder = setupFolder
        if docSettings["splitSetup"]:
            opName = constOpTmpFile
            opFolder = tempfile.gettempdir()    # e.g., C:\Users\Tim\AppData\Local\Temp
            opFolder = opFolder.replace("\\", "/")

        parameters.itemByName("nc_program_openInEditor").value.value = False
        AssignOutputFolder(parameters, opFolder)
        parameters.itemByName("nc_program_filename").value.value = opName
        parameters.itemByName("nc_program_name").value.value = fname

        # Do it all at once?
        if not docSettings["splitSetup"]:
            fileHead.close()
            try:
                program.operations = [setup]
                if not program.postProcess(adsk.cam.NCProgramPostProcessOptions.create()):
                    return "Fusion reported an error."
                time.sleep(constPostLoopDelay) # files missing sometimes unless we slow down (??)
                return None, None
            except Exception as exc:
                retVal += ": " + str(exc)
                return retVal, None

        #
        # Split setup into individual operations
        #

        opPath = opFolder + "/" + opName + fileExt
        if fileBody is None: # Use a local body file to create one file per setup rather than one large file
            fileBody = open(opFolder + "/" + constBodyTmpFile + fileExt, "w")
            firstOp = True 
            lineNum = 10
        else:
            firstOp = fileBody.tell() == 0
            if fBlankOk:
                fileBody.write(f"\n")
            fileBody.write(f"(Setup: {setup.name})\n")

        regBody = re.compile(r""
            r"(?P<N>N[0-9]+ *)?" # line number
            r"(?P<line>"         # line w/o number
            r"(M(?P<M>[0-9]+) *)?" # M-code
            r"(G(?P<G>[0-9]+) *)?" # G-code
            r"(T(?P<T>[0-9]+))?" # Tool
            r".+)",              # to end of line
            re.IGNORECASE | re.DOTALL)

        i = 0
        allOperations = setup.allOperations
        tailGcode = None
        newSetup = True

        while i < allOperations.count:
            operation = allOperations[i]
            i += 1
            
            if operation.isSuppressed:
                continue

            # Look ahead for operations without a toolpath. This can happen
            # with a manual operation. Group it with current operation.
            # Or if first, group it with subsequent ones.
            # Also optionally group together operations with the same tool number
            operationWithTool = None
            currentToolNumber = -1
            hasTool = operation.hasToolpath
            if hasTool:
                operationWithTool = operation
                currentToolNumber = operation.tool.parameters.itemByName("tool_number").value.value
            operationsList = [operation]
            while i < allOperations.count:
                operation = allOperations[i]
                if not operation.isSuppressed:
                    if operation.hasToolpath and (not docSettings["combineTool"] or operation.tool.parameters.itemByName("tool_number").value.value != currentToolNumber):
                        if not hasTool:
                            operationsList.append(operation)
                            operationWithTool = operation
                            i += 1
                        break
                    operationsList.append(operation)
                i += 1

            # Generate the gcode for the selected operation(s) 
            # and make sure that the file is present
            retries = docSettings["postRetries"]
            delay = docSettings["initialDelay"]
            while True:
                success, returnValue = GenerateOperationsGCode(program, operationsList, operationWithTool, opPath, opFolder, opName, fileExt, delay, retries)
                if success: # File was generated, carry on.
                    fileOp = returnValue
                    break
                if returnValue is None: # Timing issue..? Try again.
                    if retries <= 0:
                        return returnValue # Time to give up...
                    time.sleep(delay)
                    delay *= 2
                    retries -= 1
                else:
                    return returnValue # Some other error

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

        return None, fBlankOk

    except:
        if fileHead:
            try:
                fileHead.close()
                os.remove(fileHead.name)
            except:
                pass

        if fileBody:
            try:
                fileBody.close()
                os.remove(fileBody.name)
            except:
                pass

        if fileOp:
            try:
                fileOp.close()
                os.remove(fileOp.name)
            except:
                pass

        if ui:
            retVal += " " + traceback.format_exc()

        return retVal, fBlankOk
    
# Calls the Fusion code to generat the gcode and the post processor
def GenerateOperationsGCode(program, opList, opHasTool, opPath, opFolder, opName, fileExt, delay, retries):
    try:
        # post process the collected operation(s) into one file
        program.operations = opList
        if not program.postProcess(adsk.cam.NCProgramPostProcessOptions.create()):
            retVal = "Fusion reported an error processing operation"
            if (opHasTool != None):
                retVal += ": " +  opHasTool.name
            return False, retVal
    except Exception as exc:
        if (opHasTool != None):
            retVal += " in operation " +  opHasTool.name
        retVal += ": " + str(exc)
        return False, retVal

    time.sleep(delay) # wait for it to finish (??)

    try:
        fileOp = open(opPath, encoding="utf8", errors='replace')
        return True, fileOp
    except:
        if retries > 0:
            return False, None # There is still time for it to complete. 
        
        # Maybe the file name extension is wrong
        for file in os.listdir(opFolder):
            if file.startswith(opName):
                ext = file[len(opName):]
                if ext != fileExt:
                    return False, ("Unable to open output file. "
                        "Found the file with extension '{}' instead "
                        "of '{}'. Make sure you have the correct file "
                        "extension set in the Post Process All "
                        "dialog.".format(ext, fileExt))
                break
        return False, "Unable to open " + opPath


def PostProcessOperations(docSettings, fileHead, fileBody, fileOp, fname, newSetup, opName, firstOp, regBody, isRotated, wcsRotationAngle, knownTools, fBlankOk):
            
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

    dbg("Merge G-code for operation: " + opName)

    toolChange = docSettings["toolChange"]
    fToolChangeNum = False
    if len(toolChange) != 0:
        toolChange = toolChange.replace(":", "\n")
        toolChange += "\n"
        match = regBody.match(toolChange).groupdict()
        if match["N"] != None:
            fToolChangeNum = True
            toolChange = match["line"]
            # split into individual lines to add line numbers
            toolChange = toolChange.splitlines(True)

    fFastZenabled = docSettings["fastZ"]
    if fFastZenabled:
        regParseLine = re.compile(r""
            r"(G(?P<G>[0-9]+(\.[0-9]*)?)[^XYZF]*)?"
            r"(?P<XY>((X-?[0-9]+(\.[0-9]*)?)[^XYZF]*)?"
            r"((Y-?[0-9]+(\.[0-9]*)?)[^XYZF]*)?)"
            r"(Z(?P<Z>-?[0-9]+(\.[0-9]*)?)[^XYZF]*)?"
            r"(F(?P<F>-?[0-9]+(\.[0-9]*)?)[^XYZF]*)?",
            re.IGNORECASE)
        regGcodes = re.compile(r"G([0-9]+(?:\.[0-9]*)?)")

    # Parse end code list, splitting into G-codes and M-codes
    endCodes = docSettings["endCodes"]
    endGcodes = re.findall("G([0-9]+)", endCodes)
    endGcodeSet = set()
    for code in endGcodes:
        endGcodeSet.add(int(code))
    endMcodes = re.findall("M([0-9]+)", endCodes)
    endMcodeSet = set()
    for code in endMcodes:
        endMcodeSet.add(int(code))

    # Space between operations
    if not firstOp and fBlankOk:
        fileBody.write("\n")
    
    # Gather information from all headers and add to main header
    fBlankOk, line, knownTools = addToHeader(fileHead, fileOp, firstOp, opName, fname, docSettings["numericName"], knownTools)

    # Body starts at tool code, T
    while True:
        match = regBody.match(line).groupdict()
        line = match["line"]        # filter off line number if present
        fNum = match["N"] != None

        if (match["T"] != None):
            if not firstOp and len(toolChange) != 0:
                # have tool change G-codes to add
                if fToolChangeNum:
                    # Add line number to tool change
                    for code in toolChange:
                        fileBody.write("N" + str(lineNum) + " " + code)
                        lineNum += constLineNumInc
                else:
                    fileBody.write(toolChange)
            break

        if firstOp or line[0] == "(":
            if (fNum):
                fileBody.write("N" + str(lineNum) + " ")
                lineNum += constLineNumInc
            fileBody.write(line)
        line = fileOp.readline()
        if len(line) == 0:
            return "Tool change G-code (Txx) not found; this post processor is not compatible with Post Process All."
        if line[0] == "\n":
            fBlankOk = True

    # We're done with the head, move on to the body
    # Initialize rapid move optimizations
    fFastZ = fFastZenabled
    Gcode = None
    Zcur = None
    Zfeed = None
    fZfeedNotSet = True
    feedCur = 0
    fNeedFeed = False
    fLockSpeed = False

    if newSetup and isRotated and docSettings["rotateAAxis"]:
        angle = str(round(wcsRotationAngle * 1000) / 1000)
        fileBody.write('G90 G0 A' + angle +'\n')


    # Note that match, line, and fNum are already set
    while True:
        # End of program marker?
        endMark = match["M"]
        if endMark != None:
            endMark = int(endMark)
            if endMark in endMcodeSet:
                break
            # When M49/M48 is used to turn off speed changes, disable fast moves as well
            if endMark == 49:
                fLockSpeed = True
            elif endMark == 48:
                fLockSpeed = False
        endMark = match["G"]
        if endMark != None:
            endMark = int(endMark)
            if endMark in endGcodeSet:
                break

        if fFastZ:
            # Analyze code for chances to make rapid moves
            match = regParseLine.match(line)
            if match.end() != 0:
                try:
                    match = match.groupdict()
                    Gcodes = regGcodes.findall(line)
                    fNoMotionGcode = True
                    fHomeGcode = False
                    for GcodeTmp in Gcodes:
                        GcodeTmp = int(float(GcodeTmp))
                        if GcodeTmp in constHomeGcodeSet:
                            fHomeGcode = True
                            break

                        if GcodeTmp in constMotionGcodeSet:
                            fNoMotionGcode = False
                            Gcode = GcodeTmp
                            if Gcode == 0:
                                fNeedFeed = False
                            break

                    if not fHomeGcode:
                        Ztmp = match["Z"]
                        if Ztmp != None:
                            Zlast = Zcur
                            Zcur = float(Ztmp)

                        feedTmp = match["F"]
                        if feedTmp != None:
                            feedCur = float(feedTmp)

                        XYcur = match["XY"].rstrip("\n ")

                        if (Zfeed == None or fZfeedNotSet) and (Gcode == 0 or Gcode == 1) and Ztmp != None and len(XYcur) == 0:
                            # Figure out Z feed
                            if (Zfeed != None):
                                fZfeedNotSet = False
                            Zfeed = Zcur
                            if Gcode != 0:
                                # Replace line with rapid move
                                line = constRapidZgcode.format(Zcur, line[:-1])
                                fNeedFeed = True
                                Gcode = 0

                        if Gcode == 1 and not fLockSpeed:
                            if Ztmp != None:
                                if len(XYcur) == 0 and (Zcur >= Zlast or Zcur >= Zfeed or feedCur == 0):
                                    # Upward move, above feed height, or anomalous feed rate.
                                    # Replace with rapid move
                                    line = constRapidZgcode.format(Zcur, line[:-1])
                                    fNeedFeed = True
                                    Gcode = 0

                            elif Zcur >= Zfeed:
                                # No Z move, at/above feed height
                                line = constRapidXYgcode.format(XYcur, line[:-1])
                                fNeedFeed = True
                                Gcode = 0

                        elif fNeedFeed and fNoMotionGcode:
                            # No G-code present, changing to G1
                            if Ztmp != None:
                                if len(XYcur) != 0:
                                    # Not Z move only - back to G1
                                    line = constFeedXYZgcode.format(XYcur, Zcur, feedCur, line[:-1])
                                    fNeedFeed = False
                                    Gcode = 1
                                elif Zcur < Zfeed and Zcur <= Zlast:
                                    # Not up nor above feed height - back to G1
                                    line = constFeedZgcode.format(Zcur, feedCur, line[:-1])
                                    fNeedFeed = False
                                    Gcode = 1
                                    
                            elif len(XYcur) != 0 and Zcur < Zfeed:
                                # No Z move, below feed height - back to G1
                                line = constFeedXYgcode.format(XYcur, feedCur, line[:-1])
                                fNeedFeed = False
                                Gcode = 1

                        if (Gcode != 0 and fNeedFeed):
                            if (feedTmp == None):
                                # Feed rate not present, add it
                                line = line[:-1] + constAddFeedGcode.format(feedCur)
                            fNeedFeed = False

                        if Zcur != None and Zfeed != None and Zcur >= Zfeed and Gcode != None and \
                            Gcode != 0 and len(XYcur) != 0 and (Ztmp != None or Gcode != 1):
                            # We're at or above the feed height, but made a cutting move.
                            # Feed height is wrong, bring it up
                            Zfeed = Zcur + 0.001
                except:
                    fFastZ = False # Just skip changes

        # copy line to output
        if (fNum):
            fileBody.write("N" + str(lineNum) + " ")
            lineNum += constLineNumInc
        fileBody.write(line)
        lineFull = fileOp.readline()
        if len(lineFull) == 0:
            break
        match = regBody.match(lineFull).groupdict()
        line = match["line"]        # filter off line number if present
        fNum = match["N"] != None

    # Found tail of program
    tailGcode = lineFull + fileOp.read() if firstOp else None

    fileOp.close()
    os.remove(fileOp.name)
    fileOp = None

    return tailGcode, fBlankOk

def addToHeader(fileHead, fileOp, firstOp, opName, fname, numericName, knownTools = []):

    regToolComment = re.compile(r"\((T[0-9])+\s")
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
