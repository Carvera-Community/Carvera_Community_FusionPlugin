from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Protocol

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
    path: Path | None = None
    header_source: Any | None = None
    tool_comments: tuple[Any, ...] = ()
    bodies: tuple["PlannedBody", ...] = ()
    tail_source: Any | None = None


@dataclass(frozen=True)
class PlannedBody:
    operation: Any
    rotation_angle: float | None
    preserve_rotation: bool
    is_final: bool


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


def plan_output_files(
    context: Any,
    settings: Any,
    sanitize_filename: Callable[[str], str],
) -> tuple[ResultFilePlan, ...]:
    setups = [setup for setup in context.selected if setup.ctx.operations]
    membership = plan_result_files(setups, settings.operationsGrouping)
    body_by_operation = {
        body.operation: body for body in _plan_rotations(setups, settings.rotateAAxis)
    }
    base_name = context.fileName
    numeric_name = base_name
    plans: list[ResultFilePlan] = []

    if settings.operationsGrouping == Constants.OperationsGroupings.SINGLE_FILE:
        if not membership:
            return ()
        members = membership[0]
        operations_context = members.setups[0].ctx.operations.ctx
        path = operations_context.path / f"{base_name}{operations_context.fileExtension}"
        return (_complete_plan(
            members,
            path,
            next((op for op in members.operations if op.hasHeader), None),
            members.operations,
            body_by_operation,
            next((op for op in members.operations if op.hasTail), None),
        ),)

    for setup_index, setup in enumerate(setups):
        operations = setup.ctx.operations
        body_operations = tuple(op for op in operations if op.hasBody)
        if not body_operations:
            continue

        if settings.numericName:
            setup_base_name = numeric_name
        else:
            prefix = (
                str(setup.index + 1).rjust(settings.fileSequenceDigits, "0") + "_"
                if settings.fileSequence else ""
            )
            setup_base_name = sanitize_filename(f"{prefix}{setup.name}")

        if settings.operationsGrouping == Constants.OperationsGroupings.SETUP:
            if settings.numericName:
                numeric_name = _next_numeric_name(numeric_name, settings.fileSequenceDigits)
            membership_for_setup = ResultFilePlan(
                (setup_index,), (setup,), body_operations
            )
            plans.append(_complete_plan(
                membership_for_setup,
                operations.ctx.path / f"{setup_base_name}{operations.ctx.fileExtension}",
                next((op for op in operations if op.hasHeader), None),
                tuple(operations),
                body_by_operation,
                operations.ctx.operationWithTail,
            ))
            continue

        tool_indexes: dict[int | None, int] = {}
        naming_settings = _operation_naming_settings(settings)
        for operation_index, operation in enumerate(body_operations):
            tool_indexes[operation.toolId] = tool_indexes.get(operation.toolId, 0) + 1
            file_name, next_name = _operation_file_name(
                setup_base_name,
                operation,
                tool_indexes[operation.toolId],
                naming_settings,
                sanitize_filename,
            )
            if settings.numericName:
                numeric_name = next_name
                setup_base_name = next_name
            membership_for_operation = ResultFilePlan(
                (setup_index, operation_index), (setup,), (operation,)
            )
            plans.append(_complete_plan(
                membership_for_operation,
                operations.ctx.path / f"{file_name}{operations.ctx.fileExtension}",
                operation if operation.hasHeader else next((op for op in operations if op.hasHeader), None),
                (operation,),
                body_by_operation,
                operations.ctx.operationWithTail,
            ))

    return tuple(plans)


def _complete_plan(membership, path, header_source, comments, bodies, tail_source):
    source_bodies = tuple(bodies[operation] for operation in membership.operations)
    planned_bodies = tuple(
        PlannedBody(
            body.operation,
            body.rotation_angle,
            body.preserve_rotation,
            index == len(source_bodies) - 1,
        )
        for index, body in enumerate(source_bodies)
    )
    return ResultFilePlan(
        membership.key,
        membership.setups,
        membership.operations,
        path,
        header_source,
        tuple(comments),
        planned_bodies,
        tail_source,
    )


def _plan_rotations(setups, rotate_a_axis):
    result = []
    first_setup = None
    current_rotation = None
    for setup in setups:
        rotation_angle = None
        preserve_rotation = True
        if rotate_a_axis and first_setup is not None:
            angle = setup.GetRotationAroundXAxisRelativeToDeg(first_setup)
            preserve_rotation = angle == current_rotation
            if not preserve_rotation:
                current_rotation = angle
                rotation_angle = angle
        operations = tuple(op for op in setup.ctx.operations if op.hasBody)
        for index, operation in enumerate(operations):
            result.append(PlannedBody(
                operation,
                rotation_angle if index == 0 else None,
                preserve_rotation if index == 0 else False,
                False,
            ))
        if first_setup is None:
            first_setup = setup
    return tuple(result)


def _operation_naming_settings(settings):
    from .operations.operation_file_naming import OperationFileNamingSettings
    return OperationFileNamingSettings(
        settings.operationsGrouping,
        settings.fileSequenceDigits,
        settings.numericName,
        settings.fileSequence,
    )


def _operation_file_name(*args):
    from .operations.operation_file_naming import get_operation_file_name
    return get_operation_file_name(*args)


def _next_numeric_name(name: str, digits: int) -> str:
    return str(int(name) + 1).rjust(digits, "0")
