from dataclasses import dataclass
from typing import Any, Iterable, Protocol

from .settings.constants import Constants


class PlannedSetupContext(Protocol):
    operations: Iterable[Any] | None


class PlannedSetup(Protocol):
    ctx: PlannedSetupContext


@dataclass(frozen=True)
class ResultFilePlan:
    key: tuple[int, ...]
    setups: tuple[PlannedSetup, ...]
    operations: tuple[Any, ...]


def plan_result_files(
    setups: Iterable[PlannedSetup],
    grouping: Constants.OperationsGroupings,
) -> tuple[ResultFilePlan, ...]:
    populated: list[tuple[PlannedSetup, tuple[Any, ...]]] = []
    for setup in setups:
        operations = tuple(
            operation
            for operation in (setup.ctx.operations or ())
            if operation.hasBody
        )
        if operations:
            populated.append((setup, operations))

    if grouping == Constants.OperationsGroupings.SINGLE_FILE:
        operations = tuple(op for _, items in populated for op in items)
        return (
            ResultFilePlan((0,), tuple(setup for setup, _ in populated), operations),
        ) if operations else ()

    if grouping == Constants.OperationsGroupings.SETUP:
        return tuple(
            ResultFilePlan((setup_index,), (setup,), operations)
            for setup_index, (setup, operations) in enumerate(populated)
        )

    return tuple(
        ResultFilePlan((setup_index, operation_index), (setup,), (operation,))
        for setup_index, (setup, operations) in enumerate(populated)
        for operation_index, operation in enumerate(operations)
    )


def assign_final_operations(
    setups: Iterable[PlannedSetup],
    plans: Iterable[ResultFilePlan],
) -> None:
    for setup in setups:
        for operation in setup.ctx.operations or ():
            operation.ctx.isLastOp = False
    for plan in plans:
        if plan.operations:
            plan.operations[-1].ctx.isLastOp = True
