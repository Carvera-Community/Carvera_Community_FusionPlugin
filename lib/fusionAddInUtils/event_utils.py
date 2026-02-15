import sys
from typing import Callable

import adsk.core
from .general_utils import Utils


class Events():
    """A class for managing event handlers.
    """
    _handlers = []

    @classmethod
    def add(
            cls,
            event: adsk.core.Event,
            callback: Callable,
            *,
            name: str = None,
            local_handlers: list = None
    ):
        """Adds an event handler to the specified event.

        Arguments:
        event -- The event object you want to connect a handler to.
        callback -- The function that will handle the event.
        name -- A name to use in logging errors associated with this event.
                Otherwise the name of the event object is used. This argument
                must be specified by its keyword.
        local_handlers -- A list of handlers you manage that is used to maintain
                        a reference to the handlers so they aren't released.
                        This argument must be specified by its keyword. If not
                        specified the handler is added to a global list and can
                        be cleared using the clear_handlers function. You may want
                        to maintain your own handler list so it can be managed 
                        independently for each command.

        :returns:
            The event handler that was created.  You don't often need this reference, but it can be useful in some cases.
        """   
        module = sys.modules[event.__module__]
        handler_type = module.__dict__[event.add.__annotations__['handler']]
        handler = Events._createHandler(handler_type, callback, event, name, local_handlers)
        event.add(handler)
        return handler

    @classmethod
    def clear(cls):
        """Clears the global list of handlers.
        """
        cls._handlers = []

    @classmethod
    def _createHandler(
            cls,
            handler_type,
            callback: Callable,
            event: adsk.core.Event,
            name: str = None,
            local_handlers: list = None
    ):
        handler = cls._defineHandler(handler_type, callback, name)()
        (local_handlers if local_handlers is not None else cls._handlers).append(handler)
        return handler

    @classmethod
    def _defineHandler(cls, handler_type, callback, name: str = None):
        name = name or handler_type.__name__

        class Handler(handler_type):
            def __init__(self):
                super().__init__()

            def notify(self, args):
                try:
                    callback(args)
                except:
                    Utils.handleError(name)

        return Handler
