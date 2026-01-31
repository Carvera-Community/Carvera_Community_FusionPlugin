# Assuming you have not changed the general structure of the template no modification is needed in this file.
from __future__ import annotations
from .lib.fusionAddInUtils import Events
from .lib.fusionAddInUtils import Utils
from .commands.commands import Commands


def run(context):
    try:
        Utils.log("PostProcessorUtil run")

        # This will run the start function in each of your commands as defined in commands/__init__.py
        Commands.start()

    except:
        Utils.handle_error('run')


def stop(context):
    try:
        # Remove all of the event handlers your app has created
        Events.clear()

        # This will run the start function in each of your commands as defined in commands/__init__.py
        Commands.stop()

    except:
        Utils.handle_error('stop')


##################################

# def InitAddIn():
#     ui = None
#     try:
#         ui  = adsk.core.Application.get().userInterface

#         # Create a button command definition.
#         cmdDefs = ui.commandDefinitions
#         cmdDef = cmdDefs.addButtonDefinition(Constants.constCmdDefId, Constants.constCmdName, Constants.toolTip, "resources/Command")
        
#         # Connect to the commandCreated event.
#         commandEventHandler = CommandEventHandler()
#         cmdDef.commandCreated.add(commandEventHandler)
#         Events.handlers.append(commandEventHandler)
        
#         # Get the Actions panel in the Manufacture workspace.
#         workSpace = ui.workspaces.itemById(Constants.constCAMWorkspaceId)
#         addInsPanel = workSpace.toolbarPanels.itemById(Constants.constCAMActionsPanelId)
        
#         # Add the button right after the Post Process command.
#         cmdControl = addInsPanel.controls.addCommand(cmdDef, Constants.constPostProcessControlId, False)
#         cmdControl.isPromotedByDefault = True
#         cmdControl.isPromoted = True

#     except:
#         if ui:
#             ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# def run(context):
#     global settingsMgr
#     ui = None
#     try:
#         settingsMgr = SettingsManager()
#         ui  = adsk.core.Application.get().userInterface
#         InitAddIn()

#     except:
#         if ui:
#             ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# def stop(context):
#     dbg("PostProcessAll stop")
#     ui = None
#     try:
#         ui  = adsk.core.Application.get().userInterface

#         # Clean up the UI.
#         cmdDef = ui.commandDefinitions.itemById(constCmdDefId)
#         if cmdDef:
#             cmdDef.deleteMe()
            
#         addinsPanel = ui.allToolbarPanels.itemById(constCAMActionsPanelId)
#         cmdControl = addinsPanel.controls.itemById(constCmdDefId)
#         if cmdControl:
#             cmdControl.deleteMe()
#     except:
#         if ui:
#             ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))	
