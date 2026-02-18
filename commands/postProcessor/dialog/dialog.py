from __future__ import annotations
from pathlib import Path
import tempfile
import adsk.core
import os


from ..setups.setups import Setups
from ..programs import Programs
from ..settings.settings import Settings
from ..strings import Strings

from ..const import Const
from ....lib.fusionAddInUtils.general_utils import Utils
from ....lib.fusionAddInUtils.event_utils import Events
from .. import config

from .layout.layout import PostDialogLayout
from .event_registry import EventRegistry

class PostDialog(PostDialogLayout):

    # Local list of event handlers used to maintain a reference so
    # they are not released and garbage collected.
    _local_handlers = []

    # Resource location for command icons, here we assume a sub folder in this directory named "resources".
    _ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

    # Executed when add-in is started.
    @classmethod
    def start(cls):
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # Create a command Definition.
        cmd_def = ui.commandDefinitions.addButtonDefinition( \
            config.CMD_ID, \
            config.CMD_NAME, \
            config.CMD_DESCRIPTION, \
            cls._ICON_FOLDER \
        )

        # Define an event handler for the command created event. It will be called when the button is clicked.
        Events.add(cmd_def.commandCreated, cls.commandCreated)

        # ******** Add a button into the UI so the user can run the command. ********
        # Get the target workspace the button will be created in.
        workspace = ui.workspaces.itemById(Const.CAM_WORKSPACE_ID)

        # Get the panel the button will be created in.
        panel = workspace.toolbarPanels.itemById(Const.CAM_ACTIONS_PANEL_ID)

        # Create the button command control in the UI after the specified existing command.
        control = panel.controls.addCommand(cmd_def, Const.POST_PROCESS_CONTROL_ID, False)

        # Specify if the command is promoted to the main toolbar. 
        control.isPromoted = True

    # Executed when add-in is stopped.
    @classmethod
    def stop(cls):
        # Get the various UI elements for this command
        app = adsk.core.Application.get()
        ui = app.userInterface

        workspace = ui.workspaces.itemById(Const.CAM_WORKSPACE_ID)
        panel = workspace.toolbarPanels.itemById(Const.CAM_ACTIONS_PANEL_ID)
        command_control = panel.controls.itemById(config.CMD_ID)
        command_definition = ui.commandDefinitions.itemById(config.CMD_ID)

        # Delete the button command control
        if command_control:
            command_control.deleteMe()

        # Delete the command definition
        if command_definition:
            command_definition.deleteMe()

    #
    # Event handlers
    #

    # Function that is called when a user clicks the corresponding button in the UI.
    # This defines the contents of the command dialog and connects to the command related events.
    @classmethod
    def commandCreated(cls, args: adsk.core.CommandCreatedEventArgs):
        # General logging for debug.

        app: adsk.core.Application = adsk.core.Application.get()
        doc: adsk.core.Document = app.activeDocument
        cam: adsk.cam.CAM = adsk.cam.CAM.cast(app.activeDocument.products.itemByProductType(Const.CAM_PRODUCT_ID))

        Settings.Load() # Load default settings
        Strings.set_language(Settings(Settings.LANGUAGE))  # Load language
        Programs.Load(cam) # Get the list of NCPrograms in the current document

        command = args.command

        cls.createLayout(command) # Create the the dialog inputs and structure

        #region Hook up events
        Events.add(command.execute, cls.commandExecute, local_handlers = cls._local_handlers)
        Events.add(command.inputChanged, cls.commandInputChanged, local_handlers = cls._local_handlers)
        Events.add(command.validateInputs, cls.commandValidateInput, local_handlers = cls._local_handlers)
        Events.add(command.destroy, cls.commandDestroy, local_handlers = cls._local_handlers)
        #endregion

    @classmethod
    def commandInputChanged(cls, args):
        EventRegistry.handle(args)

    # This event handler is called when the user clicks the OK button in the command dialog or 
    # is immediately called after the created event not command inputs were created for the dialog.
    @classmethod
    def commandExecute(cls, args: adsk.core.CommandEventArgs):
        # General logging for debug.

        app: adsk.core.Application = adsk.core.Application.get()
        ui = app.userInterface
        command = args.command

        alignedWCS, badOrigins, badXAxes = Setups.getWCSAlignmentIssues()
        if not alignedWCS:
            Utils.log(f'PostDialog: WCS are not aligned for setups: {badOrigins}', adsk.core.LogLevels.ErrorLogLevel)
            msg = '<i><u>Warning:</u></i><p>'
            if command.commandInputs.itemById(cls._ROTATE_A_AXIS_ID).value:
                msg += "Using 4th axis rotation while all Work Coordinate Systems isn't aligned properly may result in unexpected results, including damage to property and person.<p>"
            else:
                msg += "Some Work Coordinate Systems aren't aligned properly which may result in unexpected results, including damage to property and person.<p>"
            msg += "Do NOT use the result from this plug-in unless you have personally verified that the result can be used.<p>" 
            res = ui.messageBox(msg,
            "WARNING! Do not proceed!", 
            adsk.core.MessageBoxButtonTypes.OKCancelButtonType,
            adsk.core.MessageBoxIconTypes.CriticalIconType)
        
            if res != adsk.core.DialogResults.DialogOK:
                Utils.log('PostDialog: User cancelled operation due to unaligned WCS.', adsk.core.LogLevels.InfoLogLevel)
                return


        if not Programs.Current.machineHasAAxis:
            needAAxisRotation, setups = Setups.AAxisRotationRequired()
            if needAAxisRotation:
                Utils.log(f'PostDialog: Machine {Programs.Current.MachineName} does not support A axis but setups {setups} require A axis rotation.', adsk.core.LogLevels.WarningLogLevel)
                msg = '<i><u>Warning:</u></i><p>'
                msg += f"The selected machine '{Programs.Current.MachineName}' does not support A axis rotation, but the following setups require A axis rotation:<p>"
                for setupName, angle in setups:
                    msg += f"{setupName} ({angle}°)<p>"
                msg += "Using 4th axis rotation while the machine doesn't support it may result in unexpected results, including damage to property and person.<p>"
                msg += "Do NOT use the result from this plug-in unless you have personally verified that the result can be used.<p>" 
                res = ui.messageBox(msg,
                "WARNING! Do not proceed!", 
                adsk.core.MessageBoxButtonTypes.OKCancelButtonType,
                adsk.core.MessageBoxIconTypes.CriticalIconType)
            
                if res != adsk.core.DialogResults.DialogOK:
                    Utils.log('PostDialog: User cancelled operation due to unsupported A axis rotation.', adsk.core.LogLevels.InfoLogLevel)
                    return


        if Programs.Current is not None:
            Settings.Save(Programs.Current.attributes)  # Save settings for the current project
        else:
            app: adsk.core.Application = adsk.core.Application.get()
            doc: adsk.core.Document = app.activeDocument
            Settings.Save(doc.attributes)  # Save settings for the current project


        try:
            # Create a temporary folder to prepare all files in
            with tempfile.TemporaryDirectory() as tmpdir:
                Programs.Current.Process(Path(tmpdir))
                Programs.Current.Generate()
        except FileExistsError as e:
            Utils.log(f'PostDialog: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
            ui.messageBox(str(e), "File already exists!", adsk.core.MessageBoxButtonTypes.OKButtonType, adsk.core.MessageBoxIconTypes.CriticalIconType)
        except Exception as e:
            Utils.log(f'PostDialog: An error occurred during post processing: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
            ui.messageBox(f"An error occurred during post processing: {str(e)}", "Error!", adsk.core.MessageBoxButtonTypes.OKButtonType, adsk.core.MessageBoxIconTypes.CriticalIconType)

    # This event handler is called when the user interacts with any of the inputs in the dialog
    # which allows you to verify that all of the inputs are valid and enables the OK button.
    @classmethod
    def commandValidateInput(cls, args: adsk.core.ValidateInputsEventArgs):
        # General logging for debug.

        inputs = args.inputs
        
        args.areInputsValid = Programs.Current is not None \
            and Programs.Current.hasMachine \
            and Setups.hasSelected \
            and all(not setup.hasError for setup in Setups.selected) \
            and (Programs.Current.machineHasAAxis or not Setups.AAxisRotationRequired()[0])

        # TODO: Set up so that the Process button is only enabled when things are set up properly

        # # Verify the validity of the input values. This controls if the OK button is enabled or not.
        # valueInput = inputs.itemById('value_input')
        # if valueInput.value >= 0:
        #     args.areInputsValid = True
        # else:
        #     args.areInputsValid = False
            
    # This event handler is called when the command terminates.
    @classmethod
    def commandDestroy(cls, args: adsk.core.CommandEventArgs):
        # General logging for debug.

        cls._local_handlers = []  # clear out the local handlers list


    