from types import SimpleNamespace

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

    plans = module.planResultFiles(setups, Constants.OperationsGroupings.SINGLE_FILE)
    module.assignFinalOperations(setups, plans)

    assert len(plans) == 1
    assert plans[0].operations == (first, last)
    assert [first.ctx.isLastOp, ignored.ctx.isLastOp, last.ctx.isLastOp] == [False, False, True]


def test_setup_and_split_plans_express_result_file_membership():
    first, second, third = operation(), operation(), operation()
    setups = [setup(first, second), setup(third)]

    per_setup = module.planResultFiles(setups, Constants.OperationsGroupings.SETUP)
    split = module.planResultFiles(setups, Constants.OperationsGroupings.PER_OPERATION)

    assert [plan.operations for plan in per_setup] == [(first, second), (third,)]
    assert [plan.operations for plan in split] == [(first,), (second,), (third,)]
