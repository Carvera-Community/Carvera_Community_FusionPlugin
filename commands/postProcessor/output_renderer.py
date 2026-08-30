from pathlib import Path
from typing import Iterable

from .output_plan import ResultFilePlan


def render_output_files(
    plans: Iterable[ResultFilePlan],
    overwrite_files: bool,
) -> tuple[Path, ...]:
    written: list[Path] = []
    for plan in plans:
        if plan.path is None:
            raise ValueError("ResultFilePlan.path is not set")
        if plan.path.exists() and not overwrite_files:
            raise FileExistsError(
                f"File {plan.path} already exists and overwrite is not allowed."
            )
        plan.path.parent.mkdir(parents=True, exist_ok=True)
        with plan.path.open("w") as output:
            if plan.header_source is not None:
                plan.header_source.WriteHeaderStart(output)
                for operation in plan.tool_comments:
                    operation.WriteToolComment(output)
                plan.header_source.WriteHeaderEnd(output)

            for body in plan.bodies:
                body.operation.ctx.rotationAngle = body.rotation_angle
                body.operation.ctx.preserveRotation = body.preserve_rotation
                body.operation.ctx.isLastOp = body.is_final
                body.operation.WriteBody(output)

            if plan.tail_source is not None:
                plan.tail_source.WriteTail(output, None)
        written.append(plan.path)
    return tuple(written)
