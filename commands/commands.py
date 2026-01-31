from __future__ import annotations
from .postProcessor.dialog import PostDialog

class Commands():

    # TODO add your imported modules to this list.
    # Fusion will automatically call the start() and stop() functions.
    _commands = [
        PostDialog
    ]


    # Assumes you defined a "start" function in each of your modules.
    # The start function will be run when the add-in is started.
    @staticmethod
    def start():
        for command in Commands._commands:
            command.start()


    # Assumes you defined a "stop" function in each of your modules.
    # The stop function will be run when the add-in is stopped.
    @staticmethod
    def stop():
        for command in Commands._commands:
            command.stop()
