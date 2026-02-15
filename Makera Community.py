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
        Utils.handleError('run')


def stop(context):
    try:
        # Remove all of the event handlers your app has created
        Events.clear()

        # This will run the start function in each of your commands as defined in commands/__init__.py
        Commands.stop()

    except:
        Utils.handleError('stop')
