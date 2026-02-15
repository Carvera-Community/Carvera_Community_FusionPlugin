# ...existing code...
from collections import defaultdict
from typing import Callable, Any, List, Union

import adsk

class EventRegistry:

    _registry: dict[str, List[Callable[..., Any]]] = defaultdict(list)
    _last_values: dict[str, object] = {}

    @classmethod
    def register(cls, inputOrId: Union[adsk.core.CommandInput, str], callback: Callable[..., Any]):
        """Register a callback for an input object or input id.
        Callback signature: callback(input_obj, args) or callback(args)."""
        if isinstance(inputOrId, adsk.core.CommandInput):
            cls._registry[inputOrId.id].append(callback)
        else:
            cls._registry[inputOrId].append(callback)

    @classmethod
    def registerWithOnlyChange(cls, inputOrId: Union[adsk.core.CommandInput, str], callback: Callable[..., Any]):
        """Register callback but ignore duplicate ValueChanged events that don't 
        change .value by creating a wrapper that tracks the last known value for the input."""
        # try to seed initial value if we have the object
        if isinstance(inputOrId, adsk.core.CommandInput):
            cls._last_values[inputOrId.id] = inputOrId.value

        def _wrapped(input):
            current = input.value
            prev = cls._last_values.get(input.id, None)
            if prev is not None and current == prev:
                return  # duplicate event, ignore
            cls._last_values[input.id] = current
            callback(input)

        cls.register(inputOrId, _wrapped)

    @classmethod
    def setValue(cls, inputOrId: Union[adsk.core.CommandInput, str], value):
        """Set the value of an input and update the registry's last known value to prevent false duplicate events."""
        if isinstance(inputOrId, adsk.core.CommandInput):
            input_id = inputOrId.id
            cls._last_values[input_id] = value
            inputOrId.value = value
        else:
            input_id = inputOrId
            cls._last_values[input_id] = value

    @classmethod
    def unregister(cls, inputOrId: Union[adsk.core.CommandInput, str], callback = None):
        """Unregister a callback for an input object or input id. If callback is None, unregister all callbacks for the input."""
        if isinstance(inputOrId, adsk.core.CommandInput):
            input_id = inputOrId.id
        else:
            input_id = inputOrId

        if callback is None:
            cls._registry.pop(input_id, None)
        else:
            lst = cls._registry.get(input_id)
            if lst and callback in lst:
                lst.remove(callback)
                if not lst:
                    cls._registry.pop(input_id, None)

    @classmethod
    def handle(cls, args):
        """Call from your global commandInputChanged handler."""
        if not isinstance(args, adsk.core.InputChangedEventArgs):
            return
        input: adsk.core.CommandInput = args.input
        for callback in list(cls._registry.get(input.id, [])):
            try:
                try:
                    callback(input)
                except TypeError:
                    callback(args)
            except Exception:
                pass
