from collections import defaultdict
from typing import Callable, Any, List, Union

from adsk.core import (
    CommandInput,
    InputChangedEventArgs
)

class EventRegistry:

    _registry: dict[str, List[Callable[..., Any]]] = defaultdict(list)
    _last_values: dict[str, object] = {}

    @classmethod
    def register(cls, id: str, callback: Callable[..., Any]):
        """Register a callback for an input object or input id.
        Callback signature: callback(input_obj, args) or callback(args)."""
        cls._registry[id].append(callback)

    @classmethod
    def registerWithOnlyChange(cls, id: str, callback: Callable[..., Any]):
        """Register callback but ignore duplicate ValueChanged events that don't 
        change .value by creating a wrapper that tracks the last known value for the input."""
        # try to seed initial value if we have the object

        def _wrapped(input):
            current = input.value
            prev = cls._last_values.get(input.id, None)
            if prev is not None and current == prev:
                return  # duplicate event, ignore
            cls._last_values[input.id] = current
            callback(input)

        cls.register(id, _wrapped)

    @classmethod
    def setValue(cls, id: str, value):
        """Set the value of an input and update the registry's last known value to prevent false duplicate events."""
        cls._last_values[id] = value

    @classmethod
    def unregister(cls, id: str, callback = None):
        """Unregister a callback for an input object or input id. If callback is None, unregister all callbacks for the input."""
        if callback is None:
            cls._registry.pop(id, None)
        else:
            lst = cls._registry.get(id)
            if lst and callback in lst:
                lst.remove(callback)
                if not lst:
                    cls._registry.pop(id, None)

    @classmethod
    def handle(cls, args):
        """Call from your global commandInputChanged handler."""
        if not isinstance(args, InputChangedEventArgs):
            return
        input: CommandInput = args.input
        for callback in list(cls._registry.get(input.id, [])):
            try:
                try:
                    callback(input)
                except TypeError:
                    callback(args)
            except Exception:
                pass
