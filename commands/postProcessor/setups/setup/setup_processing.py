from pathlib import Path
from typing import Any, Callable

from ...operations.operations_context import OperationsContext
from ..setup_source import raw_setup


def create_operations(
    context: Any,
    fusion_adapter: Any,
    operations_factory: Callable,
):
    """Create the operation collection for one currently viable setup."""
    if not context.isSelected or context.isSuppressed or context.hasError:
        return None

    sources = [
        operation
        for candidate in context.setup.allOperations
        if (operation := fusion_adapter.cast_operation(candidate)) is not None
    ]
    return operations_factory(
        OperationsContext(processingSettings=context.processingSettings),
        sources,
    )


def process_setup(
    context: Any,
    temp_path: Path,
    fusion_adapter: Any,
    operations_factory: Callable,
    program_registry: Any,
) -> None:
    """Generate and parse temporary operation files for one setup."""
    context.operations = create_operations(
        context,
        fusion_adapter,
        operations_factory,
    )
    if not context.operations:
        return

    program = program_registry.Current
    if program is None:
        raise ValueError("Programs.Current is None")

    program.disable_open_in_editor()
    program_registry.check_and_generate_toolpath(raw_setup(context.setup))
    context.operations.parse(temp_path, program)
