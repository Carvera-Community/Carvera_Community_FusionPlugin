from typing import Protocol


class AttributeCollection(Protocol):
    count: int

    def __iter__(self): ...
    def itemByName(self, group: str, name: str): ...
    def add(self, group: str, name: str, value: str): ...

class _AttributesMeta(type):
    _attributes: AttributeCollection
    
    def __iter__(cls):
        return iter(cls._attributes)

class Attributes(metaclass=_AttributesMeta):
    def __init__(self, attributes: AttributeCollection):
        self._attributes = attributes

    def add(self, group, name, value):
        """Sets or adds an attribute associated with the Fusion NCProgram"""
        attr = self._attributes.itemByName(group, name)
        if attr is None:
            self._attributes.add(group, name, value)
        else:
            attr.value = value

    def get(self, group, name):
        """Returns an attribute value associated with the Fusion NCProgram"""
        attr = self._attributes.itemByName(group, name)
        if attr is not None:
            return attr.value
        return None
    
    def itemByName(self, group, name):
        """Returns the attribute item associated with the Fusion NCProgram"""
        return self._attributes.itemByName(group, name)
    
    @property
    def count(self):
        """Returns the number of attributes associated with the Fusion NCProgram"""
        return self._attributes.count
