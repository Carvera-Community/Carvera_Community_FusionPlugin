from types import SimpleNamespace

import pytest

from addin_import import import_addin_module


Parameters = import_addin_module("commands.postProcessor.parameters").Parameters


class FakeCollection:
    def __init__(self, values):
        self.values = {
            name: SimpleNamespace(name=name, value=value)
            for name, value in values.items()
        }

    def itemByName(self, name):
        return self.values.get(name)


class FakeValueAdapter:
    def get(self, parameter, value_type):
        if not isinstance(parameter.value, value_type):
            raise TypeError(f"{parameter.name} has wrong type")
        return parameter.value

    def set(self, parameter, value):
        if type(parameter.value) is not type(value):
            raise TypeError(f"{parameter.name} has wrong type")
        parameter.value = value


def parameters(values):
    return Parameters(FakeCollection(values), FakeValueAdapter())


@pytest.mark.parametrize(
    ("value", "value_type"),
    [(7, int), (2.5, float), (True, bool), ("job", str)],
)
def test_get_returns_typed_parameter_value(value, value_type):
    instance = parameters({"parameter": value})

    assert instance.Get("parameter", value_type) == value


def test_get_returns_none_for_missing_parameter():
    assert parameters({}).Get("missing", str) is None


def test_get_rejects_unsupported_requested_type():
    instance = parameters({"parameter": [1]})

    with pytest.raises(TypeError, match="Unhandled type"):
        instance.Get("parameter", list)


@pytest.mark.parametrize("value", [8, 3.5, False, "updated"])
def test_set_updates_parameter_through_adapter(value):
    instance = parameters({"parameter": type(value)()})

    instance.Set("parameter", value)

    assert instance.Get("parameter", type(value)) == value


def test_set_rejects_missing_parameter():
    with pytest.raises(KeyError, match="does not exist"):
        parameters({}).Set("missing", "value")


def test_set_preserves_adapter_type_validation():
    instance = parameters({"parameter": "text"})

    with pytest.raises(TypeError, match="wrong type"):
        instance.Set("parameter", 4)
