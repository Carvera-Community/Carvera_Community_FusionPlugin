from pathlib import Path
import re
from types import SimpleNamespace

import pytest

from addin_import import import_addin_module


analysis_module = import_addin_module(
    "commands.postProcessor.operations.operation.analysis"
)
body_writer = import_addin_module(
    "commands.postProcessor.operations.operation.body_writer"
)
header_writer = import_addin_module(
    "commands.postProcessor.operations.operation.header_writer"
)
tail_writer = import_addin_module(
    "commands.postProcessor.operations.operation.tail_writer"
)
OperationContext = import_addin_module(
    "commands.postProcessor.operations.operation.operation_context"
).OperationContext
ProcessingSettings = import_addin_module(
    "commands.postProcessor.processing_settings"
).ProcessingSettings
Constants = import_addin_module(
    "commands.postProcessor.settings.constants"
).Constants
output_plan = import_addin_module("commands.postProcessor.output_plan")
output_renderer = import_addin_module("commands.postProcessor.output_renderer")


class StreamingOperation:
    def __init__(self, root: Path, index: int, name: str, tool_id: int, settings):
        self.index = index
        self.name = name
        self.tool_id = tool_id
        self.has_header = True
        self.has_body = True
        self.has_tail = True
        source = root / f"{name}.tmp"
        source.write_text(
            f"({source.stem})\n"
            "(HEADER)\n"
            f"(T{tool_id} tool)\n"
            "G21\n"
            f"(BODY {name})\n"
            "G92.4 A0 R0\n"
            "M5\n"
            "M30\n",
            encoding="utf-8",
        )
        self.ctx = OperationContext(index, name=name, processingSettings=settings)
        self.ctx.analysis = analysis_module.ParsedOperation(
            source_file=source,
            header=analysis_module.LineRange(0, 4),
            body=analysis_module.LineRange(4, 6),
            tail=analysis_module.LineRange(6),
            tool_comment_line=2,
            rotation_line=None,
            shrink_line=5,
            allow_blank_lines=False,
            rapid_rewrites=(),
        )

    def write_header_start(self, output):
        header_writer.write_header_start(self.ctx, output)

    def write_tool_comment(self, output):
        header_writer.write_tool_comment(self.ctx, output)

    def write_header_end(self, output):
        header_writer.write_header_end(self.ctx, output)

    def write_body(self, output):
        body_writer.write_body(self.ctx, output)

    def write_tail(self, output):
        tail_writer.write_tail(self.ctx, output)


class OperationCollection:
    def __init__(self, output_path: Path, operations):
        self._operations = operations
        self.ctx = SimpleNamespace(
            path=output_path,
            file_extension=".nc",
            operation_with_tail=operations[0],
        )

    def __iter__(self):
        return iter(self._operations)

    def __len__(self):
        return len(self._operations)


class PlannedSetup:
    def __init__(self, index: int, name: str, output_path: Path, operations):
        self.index = index
        self.name = name
        self.ctx = SimpleNamespace(
            operations=OperationCollection(output_path, operations)
        )

    def rotation_relative_to_degrees(self, _other):
        return 0.0


def settings(grouping):
    return ProcessingSettings(
        operationsGrouping=grouping,
        combineTool=False,
        flatFileStructure=True,
        numericName=False,
        clearFolder=False,
        fileSequence=False,
        fileSequenceDigits=3,
        overwriteFiles=False,
        rotateAAxis=False,
        safeYRetraction=False,
        yRetractionCoordinate=-100,
        restoreRapidMoves=False,
        rapidMovesMinimumDistance=20,
        rapidMovesMaxSteps=3,
        headerEndCodes="G21",
        endCodes="M5 M30",
    )


def build_context(tmp_path, grouping):
    current = settings(grouping)
    specifications = [
        ("Top", (("A1", 1), ("A2", 1), ("A3", 2), ("A4", 1))),
        ("Side", (("B1", 3), ("B2", 3))),
    ]
    setups = []
    operation_index = 0
    for setup_index, (setup_name, items) in enumerate(specifications):
        operations = []
        for operation_name, tool_id in items:
            operations.append(
                StreamingOperation(
                    tmp_path,
                    operation_index,
                    operation_name,
                    tool_id,
                    current,
                )
            )
            operation_index += 1
        setups.append(PlannedSetup(setup_index, setup_name, tmp_path, operations))
    return SimpleNamespace(selected=setups, file_name="job"), current


@pytest.mark.parametrize(
    ("grouping", "expected"),
    [
        (
            Constants.OperationsGroupings.SINGLE_FILE,
            {"job.nc": ("A1", "A2", "A3", "A4", "B1", "B2")},
        ),
        (
            Constants.OperationsGroupings.SETUP,
            {
                "Top.nc": ("A1", "A2", "A3", "A4"),
                "Side.nc": ("B1", "B2"),
            },
        ),
        (
            Constants.OperationsGroupings.SETUP_AND_TOOL,
            {
                "Top_T1.nc": ("A1", "A2"),
                "Top_T2.nc": ("A3",),
                "Top_T1_2.nc": ("A4",),
                "Side_T3.nc": ("B1", "B2"),
            },
        ),
        (
            Constants.OperationsGroupings.PER_OPERATION,
            {
                "A1.nc": ("A1",),
                "A2.nc": ("A2",),
                "A3.nc": ("A3",),
                "A4.nc": ("A4",),
                "B1.nc": ("B1",),
                "B2.nc": ("B2",),
            },
        ),
    ],
)
def test_complete_streaming_output_for_every_grouping(tmp_path, grouping, expected):
    context, current = build_context(tmp_path, grouping)
    plans = output_plan.plan_output_files(context, current, lambda name: name)

    paths = output_renderer.render_output_files(plans, overwrite_files=False)

    assert {path.name for path in paths} == set(expected)
    for path in paths:
        contents = path.read_text(encoding="utf-8")
        members = expected[path.name]
        assert re.findall(r"^\(BODY ([^)]+)\)$", contents, re.MULTILINE) == list(members)
        assert contents.count("G92.4 A0 R0") == 1
        assert contents.count("M30") == 1
        positions = [contents.index(f"(BODY {name})") for name in members]
        assert positions == sorted(positions)
