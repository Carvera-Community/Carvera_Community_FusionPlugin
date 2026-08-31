from types import SimpleNamespace

from addin_import import import_addin_module


Attributes = import_addin_module("commands.postProcessor.attributes").Attributes


class FakeAttributes:
    def __init__(self):
        self.items = {}

    @property
    def count(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items.values())

    def itemByName(self, group, name):
        return self.items.get((group, name))

    def add(self, group, name, value):
        self.items[(group, name)] = SimpleNamespace(value=value)


def test_add_creates_and_updates_attribute():
    source = FakeAttributes()
    attributes = Attributes(source)

    attributes.add("group", "name", "first")
    attributes.add("group", "name", "updated")

    assert attributes.get("group", "name") == "updated"
    assert attributes.count == 1


def test_get_returns_none_for_missing_attribute():
    assert Attributes(FakeAttributes()).get("group", "missing") is None


def test_item_by_name_exposes_underlying_attribute():
    source = FakeAttributes()
    source.add("group", "name", "value")

    assert Attributes(source).itemByName("group", "name").value == "value"
