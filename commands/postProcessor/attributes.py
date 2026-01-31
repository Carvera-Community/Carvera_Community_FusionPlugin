import adsk.core


class Attributes:
    def __init__(self, attributes: adsk.core.Attributes):
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
    