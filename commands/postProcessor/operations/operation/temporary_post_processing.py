from dataclasses import dataclass
from pathlib import Path
import time
from typing import Callable, Protocol, TypeVar
import uuid


class TemporaryOperationContext(Protocol):
    name: str
    tempFilePath: Path


SourceOperation = TypeVar("SourceOperation")


@dataclass(frozen=True)
class TemporaryPostProcessPolicy:
    initialDelay: float = 0.1
    maxAttempts: int = 10


def createTemporaryOperationFile(
    ctx: TemporaryOperationContext,
    tempPath: Path,
    operations: list[SourceOperation],
    fileExtension: str | None,
    postProcess: Callable[[list[SourceOperation], Path, str], bool],
    parseOperationFile: Callable[[TemporaryOperationContext], None],
    policy: TemporaryPostProcessPolicy = TemporaryPostProcessPolicy(),
    createId: Callable[[], str] = lambda: uuid.uuid4().hex,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    name = createId() + ("" if fileExtension is None else fileExtension)
    ctx.tempFilePath = tempPath / name

    if not postProcess(operations, ctx.tempFilePath.parent, ctx.tempFilePath.stem):
        raise RuntimeError(f"Operation {ctx.name} post processing failed.")

    attempts = 0
    while not ctx.tempFilePath.exists() and attempts < policy.maxAttempts:
        attempts += 1
        sleep(policy.initialDelay * attempts)

    if not ctx.tempFilePath.exists():
        raise RuntimeError(
            f"Operation {ctx.name} post processing failed: "
            "output file was not created."
        )

    parseOperationFile(ctx)
