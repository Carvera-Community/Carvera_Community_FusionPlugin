from __future__ import annotations
from pathlib import Path
import tempfile
from typing import cast
from adsk.core import (
    Application,
    BoolValueCommandInput,
    CommandControl,
    CommandCreatedEventArgs,
    CommandEventArgs,
    DialogResults,
    Document,
    LogLevels,
    MessageBoxButtonTypes,
    MessageBoxIconTypes,
    ValidateInputsEventArgs
)
from adsk.cam import CAM
import os


from ..setups.setups import (
    a_axis_rotation_required,
    get_wcs_alignment_issues
)
from ..programs import Programs
from ..settings.settings import Settings
from ..strings import Strings

from ..const import Const
from ....lib.fusionAddInUtils.general_utils import Utils
from ....lib.fusionAddInUtils.event_utils import Events
from .. import config
from ..setups.setups_context import SetupsContext

from .layout.layout import PostDialogLayout
from .event_registry import EventRegistry
from .state import can_process

class PostDialog(PostDialogLayout):

    # Local list of event handlers used to maintain a reference so
    # they are not released and garbage collected.
    _local_handlers = []

    _ctx: SetupsContext

    # Resource location for command icons, here we assume a sub folder in this directory named "resources".
    _ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

    # Executed when add-in is started.
    @classmethod
    def start(cls):
        app = Application.get()
        ui = app.userInterface

        cls._ctx = SetupsContext()

        # ******** Add a button into the UI so the user can run the command. ********
        # Get the target workspace the button will be created in.
        workspace = ui.workspaces.itemById(Const.CAM_WORKSPACE_ID)
        # Get the panel the button will be created in.
        panel = workspace.toolbarPanels.itemById(Const.CAM_ACTIONS_PANEL_ID)

        # Always switch to Select to terminate any lingering command dialog from
        # a previous debug session before trying to delete/recreate definitions.
        select_command = ui.commandDefinitions.itemById('SelectCommand')
        if select_command:
            try:
                select_command.execute()
            except Exception:
                Utils.log(
                    'PostDialog.start: Failed to execute SelectCommand while resetting stale UI state.',
                    LogLevels.WarningLogLevel
                )

        # Hard-reset stale UI objects from previous debug sessions.
        old_control = panel.controls.itemById(config.CMD_ID)
        if old_control:
            try:
                old_control.deleteMe()
            except Exception:
                Utils.log(
                    'PostDialog.start: Existing command control could not be deleted. '
                    'A stale control from a previous debug session may remain.',
                    LogLevels.WarningLogLevel
                )

        old_definition = ui.commandDefinitions.itemById(config.CMD_ID)
        if old_definition:
            try:
                old_definition.deleteMe()
            except Exception:
                Utils.log(
                    'PostDialog.start: Existing command definition could not be deleted. '
                    'Fusion may keep it alive while an old dialog/session is still active.',
                    LogLevels.WarningLogLevel
                )

        # Create a fresh command definition for this session. If Fusion still keeps
        # the old one alive, reuse it instead of crashing with duplicate-id.
        cmd_def = ui.commandDefinitions.itemById(config.CMD_ID)
        if cmd_def is None:
            try:
                cmd_def = ui.commandDefinitions.addButtonDefinition(
                    config.CMD_ID,
                    config.CMD_NAME,
                    config.CMD_DESCRIPTION,
                    cls._ICON_FOLDER
                )
            except RuntimeError:
                Utils.log(
                    'PostDialog.start: addButtonDefinition reported duplicate command id. '
                    'Reusing existing definition (likely stale UI state from previous debug session).',
                    LogLevels.WarningLogLevel
                )
                cmd_def = ui.commandDefinitions.itemById(config.CMD_ID)
                if cmd_def is None:
                    Utils.log(
                        'PostDialog.start: Duplicate-id fallback failed because command definition was not found after addButtonDefinition error.',
                        LogLevels.ErrorLogLevel
                    )
                    raise

        # Define an event handler for the command created event. It will be called when the button is clicked.
        Events.add(cmd_def.commandCreated, cls.commandCreated)

        # Create the button command control in the UI after the specified existing command.
        control = CommandControl.cast(panel.controls.itemById(config.CMD_ID))
        if control is None:
            control = panel.controls.addCommand(cmd_def, Const.POST_PROCESS_CONTROL_ID, False)
        else:
            Utils.log(
                'PostDialog.start: Reusing existing command control. '
                'If the button does not respond, restart the debug session with the dialog closed.',
                LogLevels.WarningLogLevel
            )

        # Specify if the command is promoted to the main toolbar. 
        control.isPromoted = True

    # Executed when add-in is stopped.
    @classmethod
    def stop(cls):
        # Get the various UI elements for this command
        app = Application.get()
        ui = app.userInterface

        doc: Document = app.activeDocument
        Settings.save(doc.attributes)  # Save settings for the current document

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

        cls._local_handlers = []  # clear out the local handlers list
        del cls._ctx # Clear out the current Setups context

    #
    # Event handlers
    #

    # Function that is called when a user clicks the corresponding button in the UI.
    # This defines the contents of the command dialog and connects to the command related events.
    @classmethod
    def commandCreated(cls, args: CommandCreatedEventArgs):
        # General logging for debug.

        app: Application = Application.get()
        doc: Document = app.activeDocument
        cam = CAM.cast(app.activeDocument.products.itemByProductType(Const.CAM_PRODUCT_ID))

        Settings.load(doc.attributes) # Load settings from the document
        Strings.set_language(Settings(Settings.LANGUAGE))  # Load language
        Programs.load(
            cls._ctx,
            cam,
            selectedProgramName=Settings(Settings.NC_PROGRAM),
        ) # Get the list of NCPrograms in the current document

        command = args.command

        cls.createLayout(command, cls._ctx) # Create the the dialog inputs and structure

        #region Hook up events
        Events.add(command.execute, cls.commandExecute, local_handlers = cls._local_handlers)
        Events.add(command.destroy, cls.commandDestroy, local_handlers = cls._local_handlers)
        Events.add(command.inputChanged, cls.commandInputChanged, local_handlers = cls._local_handlers)
        Events.add(command.validateInputs, cls.commandValidateInput, local_handlers = cls._local_handlers)
        #endregion

    @classmethod
    def commandInputChanged(cls, args):
        EventRegistry.handle(args)

    @classmethod
    def commandDestroy(cls, _args: CommandEventArgs):
        """Keep dialog changes with the document when the command closes."""
        document = Application.get().activeDocument
        if document is not None:
            Settings.save_document(document.attributes)

    # This event handler is called when the user clicks the OK button in the command dialog or 
    # is immediately called after the created event not command inputs were created for the dialog.
    @classmethod
    def commandExecute(cls, args: CommandEventArgs):
        # General logging for debug.

        app: Application = Application.get()
        ui = app.userInterface
        command = args.command

        alignedWCS, badOrigins, badXAxes = get_wcs_alignment_issues(cls._ctx)
        if not alignedWCS:
            Utils.log(f'PostDialog: WCS are not aligned for setups: {badOrigins}', LogLevels.ErrorLogLevel)
            msg = '<i><u>Warning:</u></i><p>'
            if BoolValueCommandInput.cast(command.commandInputs.itemById(cls.ROTATE_A_AXIS_ID)).value:
                msg += "Using 4th axis rotation while all Work Coordinate Systems isn't aligned properly may result in unexpected results, including damage to property and person.<p>"
            else:
                msg += "Some Work Coordinate Systems aren't aligned properly which may result in unexpected results, including damage to property and person.<p>"
            msg += "Do NOT use the result from this plug-in unless you have personally verified that the result can be used.<p>" 
            res = cast(DialogResults, ui.messageBox(msg,
            "WARNING! Do not proceed!", 
            cast(MessageBoxButtonTypes, MessageBoxButtonTypes.OKCancelButtonType),
            cast(MessageBoxIconTypes, MessageBoxIconTypes.CriticalIconType)))
        
            if res != DialogResults.DialogOK:
                Utils.log('PostDialog: User cancelled operation due to unaligned WCS.', LogLevels.InfoLogLevel)
                return


        if Programs.Current is not None and not Programs.Current.machine_has_a_axis:
            needAAxisRotation, setups = a_axis_rotation_required(cls._ctx)
            if needAAxisRotation:
                Utils.log(f'PostDialog: Machine {Programs.Current.machine_name} does not support A axis but setups {setups} require A axis rotation.', LogLevels.WarningLogLevel)
                msg = '<i><u>Warning:</u></i><p>'
                msg += f"The selected machine '{Programs.Current.machine_name}' does not support A axis rotation, but the following setups require A axis rotation:<p>"
                for setupName, angle in setups:
                    msg += f"{setupName} ({angle}°)<p>"
                msg += "Using 4th axis rotation while the machine doesn't support it may result in unexpected results, including damage to property and person.<p>"
                msg += "Do NOT use the result from this plug-in unless you have personally verified that the result can be used.<p>" 
                res = ui.messageBox(msg,
                "WARNING! Do not proceed!", 
                cast(MessageBoxButtonTypes, MessageBoxButtonTypes.OKCancelButtonType),
                cast(MessageBoxIconTypes, MessageBoxIconTypes.CriticalIconType))
            
                if res != DialogResults.DialogOK:
                    Utils.log('PostDialog: User cancelled operation due to unsupported A axis rotation.', LogLevels.InfoLogLevel)
                    return

        try:
            # Create a temporary folder to prepare all files in
            if Programs.Current is not None:
                with tempfile.TemporaryDirectory() as tmpdir:
                    Programs.Current.process(cls._ctx, Path(tmpdir))
                    Programs.Current.write_output(cls._ctx)
        except FileExistsError as e:
            Utils.log(f'PostDialog: {str(e)}', LogLevels.ErrorLogLevel)
            ui.messageBox(str(e), "File already exists!", cast(MessageBoxButtonTypes, MessageBoxButtonTypes.OKButtonType), cast(MessageBoxIconTypes, MessageBoxIconTypes.CriticalIconType))
        except Exception as e:
            Utils.log(f'PostDialog: An error occurred during post processing: {str(e)}', LogLevels.ErrorLogLevel)
            ui.messageBox(f"An error occurred during post processing: {str(e)}", "Error!", cast(MessageBoxButtonTypes, MessageBoxButtonTypes.OKButtonType), cast(MessageBoxIconTypes, MessageBoxIconTypes.CriticalIconType))

    # This event handler is called when the user interacts with any of the inputs in the dialog
    # which allows you to verify that all of the inputs are valid and enables the OK button.
    @classmethod
    def commandValidateInput(cls, args: ValidateInputsEventArgs):
        # General logging for debug.

        args.areInputsValid = can_process(Programs.Current, cls._ctx)
