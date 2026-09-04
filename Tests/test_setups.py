from types import SimpleNamespace

from addin_import import import_addin_module


setups_module = import_addin_module("commands.postProcessor.setups.setups")


class ComparablePoint:
    def __init__(self, value):
        self.value = value

    def isEqualTo(self, other):
        return self.value == other.value


class ComparableAxis:
    def __init__(self, value):
        self.value = value

    def isParallelTo(self, other):
        return self.value == other.value


class FakeSetup:
    def __init__(self, name, origin, axis, angle=0):
        self.name = name
        self.origin = ComparablePoint(origin)
        self.x_normal = ComparableAxis(axis)
        self.angle = angle

    def rotation_relative_to_degrees(self, other):
        return other.angle


def test_wcs_alignment_reports_origin_and_axis_issues():
    context = SimpleNamespace(
        selected=[
            FakeSetup("First", 0, "X"),
            FakeSetup("Moved", 1, "X"),
            FakeSetup("Rotated", 0, "Y"),
        ]
    )

    aligned, origins, axes = setups_module.get_wcs_alignment_issues(context)

    assert not aligned
    assert origins == ["Moved"]
    assert axes == ["Rotated"]


def test_wcs_alignment_accepts_matching_setups():
    context = SimpleNamespace(
        selected=[FakeSetup("First", 0, "X"), FakeSetup("Second", 0, "X")]
    )

    assert setups_module.get_wcs_alignment_issues(context) == (True, [], [])


def test_rotation_required_reports_nonzero_rounded_angles(monkeypatch):
    messages = []
    monkeypatch.setattr(setups_module, "_log", messages.append)
    context = SimpleNamespace(
        selected=[
            FakeSetup("First", 0, "X"),
            FakeSetup("Same", 0, "X", angle=0.0004),
            FakeSetup("Tilted", 0, "X", angle=12.3456),
        ]
    )

    required, rotations = setups_module.a_axis_rotation_required(context)

    assert required
    assert rotations == [("Tilted", 12.346)]
    assert messages == ["Setups: WCS needs rotation: 12.346 degrees difference."]


def test_rotation_not_required_for_single_setup():
    context = SimpleNamespace(selected=[FakeSetup("Only", 0, "X")])

    assert setups_module.a_axis_rotation_required(context) == (False, [])
