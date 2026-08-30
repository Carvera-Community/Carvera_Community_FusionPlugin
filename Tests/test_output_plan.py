from types import SimpleNamespace

import pytest

from addin_import import import_addin_module


module = import_addin_module("commands.postProcessor.output_plan")
Constants = import_addin_module("commands.postProcessor.settings.constants").Constants


def operation(has_body=True):
    return SimpleNamespace(hasBody=has_body, ctx=SimpleNamespace(isLastOp=False))


def setup(*operations):
    return SimpleNamespace(ctx=SimpleNamespace(operations=list(operations)))


def test_single_file_plan_contains_all_body_operations_in_order():
    first, ignored, last = operation(), operation(False), operation()
    setups = [setup(first, ignored), setup(last)]

    plans = module.plan_result_files(setups, Constants.OperationsGroupings.SINGLE_FILE)
    module.assign_final_operations(setups, plans)

    assert len(plans) == 1
    assert plans[0].operations == (first, last)
    assert [first.ctx.isLastOp, ignored.ctx.isLastOp, last.ctx.isLastOp] == [False, False, True]


def test_setup_and_split_plans_express_result_file_membership():
    first, second, third = operation(), operation(), operation()
    setups = [setup(first, second), setup(third)]

    per_setup = module.plan_result_files(setups, Constants.OperationsGroupings.SETUP)
    split = module.plan_result_files(setups, Constants.OperationsGroupings.PER_OPERATION)

    assert [plan.operations for plan in per_setup] == [(first, second), (third,)]
    assert [plan.operations for plan in split] == [(first,), (second,), (third,)]


class FullOperation:
    def __init__(self, name, tool_id, *, header=True, tail=True):
        self.name = name
        self.toolId = tool_id
        self.hasBody = True
        self.hasHeader = header
        self.hasTail = tail
        self.ctx = SimpleNamespace(isLastOp=False)


class FullOperations:
    def __init__(self, path, operations):
        self._items = operations
        self.ctx = SimpleNamespace(
            path=path,
            fileExtension=".nc",
            operationWithTail=next((item for item in operations if item.hasTail), None),
        )

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)


class FullSetup:
    def __init__(self, index, name, path, operations, angle=0):
        self.index = index
        self.name = name
        self.ctx = SimpleNamespace(operations=FullOperations(path, operations))
        self.angle = angle

    def rotation_relative_to_degrees(self, other):
        return self.angle


def full_settings(grouping, **overrides):
    values = {
        "operationsGrouping": grouping,
        "numericName": False,
        "fileSequence": False,
        "fileSequenceDigits": 3,
        "rotateAAxis": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_complete_single_file_plan_selects_sources_and_rotation(tmp_path):
    first = FullOperation("rough", 1)
    second = FullOperation("finish", 2)
    setups = [
        FullSetup(0, "Top", tmp_path, [first]),
        FullSetup(1, "Side", tmp_path, [second], angle=45),
    ]
    context = SimpleNamespace(selected=setups, fileName="job")

    plans = module.plan_output_files(
        context,
        full_settings(Constants.OperationsGroupings.SINGLE_FILE, rotateAAxis=True),
        lambda name: name,
    )

    assert len(plans) == 1
    assert plans[0].path == tmp_path / "job.nc"
    assert plans[0].header_source is first
    assert plans[0].tail_source is first
    assert [body.rotation_angle for body in plans[0].bodies] == [None, 45]
    assert [body.is_final for body in plans[0].bodies] == [False, True]


def test_complete_numeric_per_operation_plan_advances_across_setups(tmp_path):
    setups = [
        FullSetup(0, "Top", tmp_path, [FullOperation("one", 1)]),
        FullSetup(1, "Side", tmp_path, [FullOperation("two", 2)]),
    ]
    context = SimpleNamespace(selected=setups, fileName="009")

    plans = module.plan_output_files(
        context,
        full_settings(
            Constants.OperationsGroupings.PER_OPERATION,
            numericName=True,
        ),
        lambda name: name,
    )

    assert [plan.path.name for plan in plans] == ["009.nc", "010.nc"]
    assert all(plan.bodies[0].is_final for plan in plans)


def test_duplicate_operation_paths_are_rejected_before_rendering(tmp_path):
    setup = FullSetup(
        0,
        "Top",
        tmp_path,
        [FullOperation("duplicate", 1), FullOperation("duplicate", 2)],
    )
    setup.ctx.operations._items[0].index = 0
    setup.ctx.operations._items[1].index = 1
    context = SimpleNamespace(selected=[setup], fileName="job")

    with pytest.raises(ValueError, match="same path"):
        module.plan_output_files(
            context,
            full_settings(Constants.OperationsGroupings.PER_OPERATION),
            lambda name: name,
        )
