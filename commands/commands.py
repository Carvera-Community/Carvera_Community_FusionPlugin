from __future__ import annotations
from .postProcessor.dialog.dialog import PostDialog

class Commands():

    # TODO add your imported modules to this list.
    # Fusion will automatically call the start() and stop() functions.
    _commands = [
        PostDialog
    ]


    # Assumes you defined a "start" function in each of your modules.
    # The start function will be run when the add-in is started.
    @classmethod
    def start(cls):
        for command in Commands._commands:
            command.start()


    # Assumes you defined a "stop" function in each of your modules.
    # The stop function will be run when the add-in is stopped.
    @classmethod
    def stop(cls):
        for command in Commands._commands:
            command.stop()
