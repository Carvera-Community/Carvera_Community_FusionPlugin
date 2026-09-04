from dataclasses import dataclass
from typing import Callable, Protocol, TypeVar


class OperationSource(Protocol):
    isSuppressed: bool
    hasToolpath: bool


SourceOperation = TypeVar("SourceOperation", bound=OperationSource)


@dataclass(frozen=True)
class GroupedOperationSource:
    index: int
    source: OperationSource


def group_operation_sources(
    operations: list[SourceOperation],
    combineTool: bool,
    get_tool_number: Callable[[SourceOperation], int],
) -> list[list[GroupedOperationSource]]:
    groups: list[list[GroupedOperationSource]] = []
    currentGroup: list[GroupedOperationSource] = []
    currentToolNumber: int | None = None

    for index, operation in enumerate(operations):
        if operation.isSuppressed:
            continue

        if not currentGroup:
            currentGroup = [GroupedOperationSource(index, operation)]
            currentToolNumber = (
                get_tool_number(operation) if operation.hasToolpath else None
            )
            continue

        operationToolNumber = (
            get_tool_number(operation) if operation.hasToolpath else None
        )
        joinsCurrentGroup = (
            not operation.hasToolpath
            or currentToolNumber is None
            or (combineTool and operationToolNumber == currentToolNumber)
        )

        if joinsCurrentGroup:
            currentGroup.append(GroupedOperationSource(index, operation))
            if currentToolNumber is None and operation.hasToolpath:
                currentToolNumber = operationToolNumber
        else:
            groups.append(currentGroup)
            currentGroup = [GroupedOperationSource(index, operation)]
            currentToolNumber = operationToolNumber

    if currentGroup:
        groups.append(currentGroup)

    return groups
