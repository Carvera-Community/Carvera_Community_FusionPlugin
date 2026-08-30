# Makera Community Post Processor Current-Behavior Specification

Status: source-derived baseline for testability work  
Scope: repository working tree as reviewed on 2026-08-30  
Primary runtime: Autodesk Fusion Manufacture workspace

## 1. Purpose

This document defines the behavior that the testability refactoring must preserve, except where a behavior is explicitly classified as a known deviation. It separates:

- **Confirmed intent**: behavior confirmed by the project owner.
- **Source-observed behavior**: behavior implemented by the current working tree.
- **Known deviation**: behavior that is inconsistent with confirmed intent or contains a concrete defect. A refactoring is not required to preserve a known deviation.
- **Target verification**: behavior that cannot be confirmed by host/source checks alone and must be exercised inside Fusion 360.

Stable IDs use the `MCB-` prefix. Tests added during the refactoring should cite the applicable IDs.

## 2. System boundary

The add-in is a second-stage post processor. It does not replace Fusion's selected post processor. It repeatedly invokes the selected NC Program post processor for internal operation groups, analyzes the resulting temporary G-code files, and assembles one or more final result files.

Source entry points:

- [`Makera Community.py`](../Makera%20Community.py)
- [`commands/postProcessor/dialog/dialog.py`](../commands/postProcessor/dialog/dialog.py)
- [`commands/postProcessor/program.py`](../commands/postProcessor/program.py)

### Requirements

- **MCB-001 — Confirmed intent:** The add-in shall use the selected Fusion NC Program, its machine configuration, its post configuration, and its NC parameters as the source of post-processing behavior.
- **MCB-002 — Source-observed:** Starting the add-in shall register one promoted command in the CAM workspace. Stopping it shall remove the command UI and save settings to the active document.
- **MCB-003 — Source-observed:** Executing the command shall create a temporary directory, generate and parse temporary operation files, write the final output, and delete the temporary directory when execution leaves the context.
- **MCB-004 — Confirmed intent:** Generated G-code remains machine-safety-sensitive output and requires user validation before use.

## 3. Inputs and selection

`Programs.load()` loads all Fusion NC Programs and `SetupsContext.load()` loads all Fusion setups in browser order.

### Requirements

- **MCB-010 — Source-observed:** The current NC Program shall be selected from the saved NC Program name when a matching program exists.
- **MCB-011 — Source-observed:** If no valid setup is explicitly selected in Fusion, every non-suppressed, error-free setup shall be selected by default.
- **MCB-012 — Source-observed:** Setup processing order shall preserve Fusion browser order.
- **MCB-013 — Source-observed:** Suppressed setups and setups with errors shall not be considered valid output setups.
- **MCB-014 — Source-observed:** Suppressed operations shall not be placed in an internal operation group.
- **MCB-015 — Source-observed:** The Process action shall require a current NC Program, a machine, at least one selected setup, no selected setup error, and either machine A-axis support or no required setup rotation.
- **MCB-016 — Source-observed:** Misaligned selected WCS origins or X axes shall produce a warning and allow the user to cancel. Proceeding after the warning remains possible.
- **MCB-017 — Source-observed:** Required A-axis rotation on a machine reported without A-axis support shall produce a warning and allow the user to cancel.

## 4. Internal operation groups

An internal `Operation` may contain one or more Fusion operations. It is the unit passed to Fusion's NC Program post processor and, for the more granular output modes, the unit assigned to a result file.

Source: [`commands/postProcessor/operations/operations.py`](../commands/postProcessor/operations/operations.py)

### Requirements

- **MCB-020 — Confirmed intent:** Without tool combining, each toolpath-bearing Fusion operation shall begin a new internal operation group.
- **MCB-021 — Confirmed intent:** A Fusion operation without a toolpath shall be attached to the current group; leading operations without a toolpath shall be attached to the following toolpath-bearing operation when one exists.
- **MCB-022 — Confirmed intent:** When `COMBINE_TOOL` is enabled, consecutive Fusion operations using the same tool number shall be combined into one internal operation group.
- **MCB-023 — Confirmed intent:** Tool combining shall never cross an intervening tool change. For the sequence `T1, T1, T2, T1`, the groups shall be `(T1, T1)`, `(T2)`, `(T1)`.
- **MCB-024 — Source-observed:** The internal group name shall concatenate member operation names with `-`, unless the result exceeds the supported filename length, in which case a localized combined-operation name shall be used.

## 5. Temporary generation and analysis

Each internal operation group is posted independently to a UUID-based temporary file. The selected NC Program output folder, filename, program name, and open-in-editor parameter are temporarily changed as part of generation.

Sources:

- [`commands/postProcessor/operations/operation/operation.py`](../commands/postProcessor/operations/operation/operation.py)
- [`commands/postProcessor/operations/operation/parser.py`](../commands/postProcessor/operations/operation/parser.py)
- [`commands/postProcessor/line.py`](../commands/postProcessor/line.py)

### Streaming contract

- **MCB-030 — Confirmed intent:** Temporary G-code files may be large and shall not be loaded into memory as complete strings or complete line collections.
- **MCB-031 — Source-observed:** Normal operation analysis shall read a temporary file sequentially, one line at a time.
- **MCB-032 — Confirmed intent:** Future parser extraction may accept `Iterable[str]`, but production shall pass a streaming file iterator. `read()`, `readlines()`, and `list(file)` are prohibited for complete G-code files.
- **MCB-033 — Source-observed:** Small analysis metadata, including boundary line numbers and rapid-move segment metadata, may be retained in memory.
- **MCB-034 — Source-observed:** Header, body, and tail writers may reopen and sequentially scan the same temporary file in separate passes. Low bounded memory usage takes priority over minimizing sequential disk reads.

### Temporary generation

- **MCB-035 — Source-observed:** Fusion post processing shall receive exactly the Fusion operations contained in the current internal operation group.
- **MCB-036 — Source-observed:** Failure reported by Fusion post processing shall abort processing with an exception.
- **MCB-037 — Source-observed:** After post processing returns, the implementation shall wait up to ten increasing 0.1-second intervals for the temporary output file. Absence after the final interval shall abort processing.
- **MCB-038 — Source-observed:** The NC Program output folder, filename, and program name shall be restored after temporary processing, including when processing raises.

### Parsed metadata

The parser records zero-based line indexes for:

- Tool comment.
- End of header.
- Start of body.
- Start of tail.
- First qualifying A-axis rotation line.
- First qualifying shrink line.

### Recognition rules

- **MCB-040 — Source-observed:** G-codes may contain a decimal component, including `G92.4`.
- **MCB-041 — Source-observed:** G-code and parameter matching is case-insensitive.
- **MCB-042 — Source-observed:** The parameter parser recognizes ordered G, X, Y, A, R, Z, and F fields. The expression is order-dependent.
- **MCB-043 — Source-observed:** An optional leading `N` line number is recognized by the general body expression.
- **MCB-044 — Source-observed:** A tool comment matches a line ending in a parenthesized comment beginning with `T` and a numeric tool number.
- **MCB-045 — Source-observed:** Configured header-end codes are compared as strings prefixed with `G` or `M`.
- **MCB-046 — Source-observed:** The first body G- or M-code not accepted as a header-end code ends header parsing after header parsing has entered its active state.
- **MCB-047 — Source-observed:** A tool code may establish the body start and, when no earlier header end exists, establishes the preceding line as the header end.
- **MCB-048 — Source-observed:** The first configured end M-code encountered during body parsing establishes the tail start and ends further analysis.
- **MCB-049 — Confirmed intent:** Each internal operation contains at most one shrink command.

## 6. Result-file grouping

The active `OperationsGroupings` value determines how internal operation groups map to result files.

Sources:

- [`commands/postProcessor/settings/constants.py`](../commands/postProcessor/settings/constants.py)
- [`commands/postProcessor/output_plan.py`](../commands/postProcessor/output_plan.py)
- [`commands/postProcessor/output_renderer.py`](../commands/postProcessor/output_renderer.py)

| Mode | Intended result-file boundary | Last operation that retains shrink |
|---|---|---|
| `SINGLE_FILE` | One file for all selected non-empty setups | Final body operation across all result content |
| `SETUP` | One file per selected non-empty setup | Final body operation in each setup file |
| `SETUP_AND_TOOL` | One file per consecutive tool-run group within a setup | The internal operation group assigned to that file |
| `PER_OPERATION` | One file per internal operation group | The internal operation group assigned to that file |

### Requirements

- **MCB-050 — Confirmed intent:** `SINGLE_FILE` shall emit one complete result file containing selected setup bodies in selection/browser order.
- **MCB-051 — Confirmed intent:** `SETUP` shall emit one complete result file per non-empty selected setup.
- **MCB-052 — Confirmed intent:** `SETUP_AND_TOOL` shall emit one complete result file for each consecutive tool-run group. A tool that returns after another tool shall start a new file and may receive a repeated-tool suffix.
- **MCB-053 — Confirmed intent:** `PER_OPERATION` shall emit one complete result file per internal operation group. When `COMBINE_TOOL` is enabled, a file may consequently contain multiple consecutive Fusion operations using the same tool.
- **MCB-054 — Confirmed intent:** Every result file shall contain its applicable header, body content, and tail.
- **MCB-055 — Source-observed working tree:** Every body-bearing internal operation is now passed to `Operation.write_body()` regardless of grouping mode.
- **MCB-056 — Confirmed intent:** Final-operation status shall be derived from output-file membership, not from the position of the input setup alone.
- **MCB-057 — Source-observed working tree:** Before body output, all `isLastOp` flags are reset and reassigned according to the grouping table above.

## 7. Output paths and filenames

Sources:

- [`commands/postProcessor/program.py`](../commands/postProcessor/program.py)
- [`commands/postProcessor/setups/setups_context.py`](../commands/postProcessor/setups/setups_context.py)
- [`commands/postProcessor/output_plan.py`](../commands/postProcessor/output_plan.py)
- [`commands/postProcessor/operations/operation_file_naming.py`](../commands/postProcessor/operations/operation_file_naming.py)

### Requirements

- **MCB-060 — Source-observed:** The result file extension shall come from the selected NC Program post configuration.
- **MCB-061 — Source-observed:** `SINGLE_FILE`, flat-file output, and numeric naming shall place result files directly under the configured output folder.
- **MCB-062 — Source-observed:** Other non-flat output shall use the configured base filename as a root output directory.
- **MCB-063 — Source-observed:** For granular non-flat, non-numeric output, each setup shall receive a sanitized setup directory, optionally prefixed with its setup sequence number.
- **MCB-064 — Confirmed intent:** `SINGLE_FILE` shall use the configured base filename.
- **MCB-065 — Confirmed intent:** `SETUP` shall normally name each file after its setup, optionally prefixed with the setup sequence number.
- **MCB-066 — Confirmed intent:** `SETUP_AND_TOOL` shall include the setup name and tool number. Later consecutive runs that reuse a previous tool number shall use `_2`, `_3`, and subsequent suffixes as necessary.
- **MCB-067 — Confirmed intent:** `PER_OPERATION` shall normally use the internal operation-group name. Identical names may currently collide unless sequence numbering is enabled.
- **MCB-068 — Confirmed intent:** Numeric naming shall produce numeric filenames in the output-folder root, incrementing once for every result file and preserving the configured digit width.
- **MCB-069 — Confirmed intent:** Sequence numbering shall preserve browser/processing order in names. Setup directories use setup indexes; granular files use the internal operation's first Fusion operation index.
- **MCB-070 — Source-observed:** Generated names shall be sanitized before they are used as non-numeric result filenames.

## 8. Header, body, and tail assembly

### Header

- **MCB-080 — Source-observed:** `SINGLE_FILE` shall take header start and header end content from the first setup containing an operation with a detected header.
- **MCB-081 — Source-observed:** `SINGLE_FILE` shall append tool comments from all selected setups between the chosen header start and header end.
- **MCB-082 — Source-observed:** `SETUP` shall write one header from the setup's first header-bearing operation and collect the setup's tool comments.
- **MCB-083 — Source-observed:** `SETUP_AND_TOOL` and `PER_OPERATION` shall create their granular result files during header writing.
- **MCB-084 — Source-observed:** `PER_OPERATION` shall write header start, tool comment, and header end for each internal operation group.
- **MCB-085 — Source-observed:** `SETUP_AND_TOOL` shall write a header at the beginning of each internal tool-run result file.
- **MCB-086 — Source-observed:** Header creation shall refuse to overwrite an existing result file unless overwrite is enabled.

### Body

- **MCB-087 — Confirmed intent:** Internal operation bodies shall be appended in processing order to the result file selected by the active grouping and naming rules.
- **MCB-088 — Source-observed:** Only operations with a detected body start shall be written as body operations.
- **MCB-089 — Source-observed:** Body copying shall begin at `bodyStartLine` and stop before `tailStartLine`.
- **MCB-090 — Source-observed:** Input line numbers beginning with `N` shall be removed when lines are written.
- **MCB-091 — Source-observed:** Blank-line preservation is enabled for an operation after the parser encounters its first blank line.

### Tail

- **MCB-092 — Confirmed intent:** The first detected tail is the reusable tail source; it is normally found in the first operation of the applicable operation collection.
- **MCB-093 — Source-observed:** `Operations.parse()` selects the first operation with a detected tail.
- **MCB-094 — Confirmed intent:** A result file shall receive one tail after all body content assigned to that file.
- **MCB-095 — Source-observed:** Tail copying begins at the detected tail-start line and continues to end of the temporary operation file.

## 9. A-axis rotation and shrink

### Rotation

- **MCB-100 — Confirmed intent:** Selected setups are compared to the first selected setup as the rotational reference.
- **MCB-101 — Source-observed:** Rotation is computed as a signed angle around the setup's X axis, using projected Z normals and a Y-normal fallback for degenerate Z projection.
- **MCB-102 — Source-observed:** When A-axis rotation is disabled, native rotation handling is preserved according to the writer's `preserveRotation` state.
- **MCB-103 — Source-observed:** Only the first body operation in a setup receives the setup-level rotation decision.
- **MCB-104 — Source-observed:** A qualifying native rotation line is the first `G0` line with `A0` detected in the operation body.
- **MCB-105 — Source-observed:** When a new rotation must be emitted, the writer inserts a comment, a `G90 G53 G0 Z-3` retraction optionally including the configured machine-coordinate Y value, and `G90 G54 G0 A<angle>`.
- **MCB-106 — Source-observed:** Emitted angles are formatted to three decimal places with trailing zeroes and a trailing decimal point removed.

### Shrink

- **MCB-110 — Confirmed intent:** A shrink command is a `G92.4` line containing an A parameter and an R parameter; R's numeric value is not significant for recognizing its presence.
- **MCB-111 — Source-observed:** Body filtering applies shrink handling only when the A value equals zero.
- **MCB-112 — Confirmed intent:** An internal operation may contain no more than one shrink command.
- **MCB-113 — Confirmed intent:** A shrink command shall be removed when its operation is followed by another operation in the same result file.
- **MCB-114 — Confirmed intent:** The final operation in every result file shall retain its shrink command when it has one.
- **MCB-115 — Source-observed working tree:** `isLastOp` is assigned per result-file grouping immediately before body writing.

## 10. Rapid-move restoration

- **MCB-120 — Confirmed intent:** Rapid restoration is optional and disabled by default.
- **MCB-121 — Source-observed:** When enabled, the rapid analyzer identifies candidate XY travel between qualifying Z-only boundary moves and retains only valid segments meeting configured constraints.
- **MCB-122 — Source-observed:** A candidate start line containing `G1` is rewritten to `G0`; a line without a G-code receives a prefixed `G0` line.
- **MCB-123 — Source-observed:** Feed parameters are removed from the non-comment portion of a rewritten rapid-start line.
- **MCB-124 — Source-observed:** A `G1 (Rapid movement end)` line is inserted after the detected rapid segment.
- **MCB-125 — Confirmed intent:** Rapid analysis and rewriting shall remain streaming with memory proportional to bounded analysis metadata, not total file size.

## 11. Settings and persistence

Default settings are defined in [`commands/postProcessor/settings/settings.py`](../commands/postProcessor/settings/settings.py).

### Requirements

- **MCB-130 — Source-observed:** Settings shall be loaded from the active document when the command is created.
- **MCB-131 — Source-observed:** A document setting set with the current settings version shall be used directly.
- **MCB-132 — Source-observed:** Missing settings shall be populated from local defaults and then built-in defaults.
- **MCB-133 — Source-observed:** Settings shall be saved to active-document attributes when the add-in stops.
- **MCB-134 — Confirmed intent:** Overwrite and clear-folder options are safety-sensitive session choices and are not intended as persistent defaults.
- **MCB-135 — Source-observed:** Default grouping is `SETUP`; tool combining, numeric naming, flat output, A-axis rotation, rapid restoration, overwrite, and clear-folder behavior default to disabled.
- **MCB-136 — Source-observed:** Default tail markers are `M5`, `M9`, and `M30`; default header-end markers are `G20` and `G21`.

## 12. Output mutation and failure behavior

- **MCB-140 — Source-observed:** If the configured output path exists as a non-directory, output writing returns without producing output or raising a specific error.
- **MCB-141 — Source-observed:** When clear-folder behavior is enabled, every direct child of the output directory is deleted recursively for real directories and unlinked otherwise.
- **MCB-142 — Source-observed:** Failure to delete any child causes output writing to return without a specific user-facing failure.
- **MCB-143 — Source-observed:** Existing result files cause `FileExistsError` during header creation when overwrite is disabled.
- **MCB-144 — Source-observed:** Dialog execution catches `FileExistsError` and general exceptions, logs them, and displays error UI.
- **MCB-145 — Source-observed:** NC Program output parameters are restored in `finally` blocks after processing and output writing.

## 13. Known deviations and unresolved behavior

The following items describe current source behavior that should not silently become the refactoring baseline.

- **MCB-D01 — Handled in the current working tree; awaiting Fusion 360 verification — Shrink filter condition:** `_matchLine()` previously returned `row != ctx.shrinkLine`. Because a true result causes the caller to skip the line, the registered shrink row was retained in a non-final operation instead of removed. The condition now returns `row == ctx.shrinkLine`, so the registered row is skipped when the operation is not final in its result file.
- **MCB-D02 — Handled in the current working tree; awaiting Fusion 360 verification — Rapid setting bitwise OR:** Rapid minimum distance and maximum steps were previously combined with defaults using bitwise OR, which changed valid configured values. The configured values now pass through unchanged, with defaults of `20` and `3` applied only when the corresponding value is `None`.
- **MCB-D03 — Handled in the current working tree; awaiting Fusion 360 verification — Numeric tail access:** The former hierarchical tail writer referred to `Setup.SetFileName` and `setup._operations`, neither of which existed in the current `Setup` class. Numeric filename sequencing is now owned by the result-file planner, so tail writing no longer mutates filenames.
- **MCB-D04 — Handled in the current working tree; awaiting Fusion 360 verification — A-axis capability fallback:** `Program.machineHasAAxis` previously could return an uninitialized `unreadable_extra_axis` variable when no rotary axis and no matching read error were encountered. The fallback is now initialized to `False`; the existing recognized unreadable-extra-axis case still changes it to `True`.
- **MCB-D05 — Handled in the current working tree; awaiting Fusion 360 verification — Integer identity comparison:** `Operation.hasTool` previously used `is not -1`. It now uses numeric inequality (`!= -1`).
- **MCB-D06 — Duplicate per-operation names:** Without sequence numbering, identical operation-group names can resolve to the same result path.
- **MCB-D07 — Error visibility:** Some invalid output-path and deletion failures return silently instead of propagating an actionable error.
- **MCB-D08 — Target validation gap:** The newly corrected all-grouping body output and per-result-file shrink assignment have passed source checks but have not yet been executed in Fusion 360.
- **MCB-D09 — Handled in the current working tree; awaiting Fusion 360 verification — Safety-setting persistence:** Overwrite and clear-folder choices were previously serialized despite the README contract. Both keys are now excluded from document and local-default serialization and reset to `False` whenever settings are loaded.
- **MCB-D10 — Handled in the current working tree; awaiting Fusion 360 verification — Tail source in granular modes:** `SETUP_AND_TOOL` and `PER_OPERATION` previously called `WriteTail()` on each internal operation instead of reusing the first detected tail. Each result-file plan now explicitly references its reusable tail source. `SINGLE_FILE` chooses the first selected setup with a detected tail rather than selecting it by header presence.
- **MCB-D11 — Handled in the current working tree; covered by a host regression test — Rapid effective distance:** `AnalysisSegment.getEffectiveLength()` previously returned doubled combined Z travel and ignored XY travel. It now returns the greater of total XY travel and combined Z travel, matching the documented analyzer rule.

## 14. Refactoring constraints

The host-testable architecture now has the following enforced runtime boundaries:

- Processing options are captured once at execution start in an immutable
  `ProcessingSettings` snapshot and propagated through setup and operation
  contexts. Parsing, transformation, planning, and rendering require that
  explicit snapshot instead of reading mutable global settings.
- Fusion setup and operation objects are converted at the adapter boundary to
  small Python source records. Opaque raw handles are retained only for calls
  that must return to Fusion, including toolpath generation, renaming, geometry,
  and NC post processing.
- Parser results are stored as immutable `ParsedOperation`, `LineRange`, and
  `RapidRewrite` values. They contain only bounded metadata; source files remain
  on disk and are streamed again when output is rendered.
- A complete `ResultFilePlan` owns each output path, header source, tool-comment
  sources, ordered body operations, tail source, and final-operation decision.
  Shrink retention therefore follows result-file membership rather than input
  setup position.
- `output_renderer.py` opens each result file once and renders its planned
  header, bodies, and tail in order. The former setup- and collection-level
  header/body/tail writer hierarchy has been removed.
- Rapid tokenization and segment analysis live in focused modules under
  `operations/operation/rapid_moves/`; the legacy streaming state machine is
  retained as the orchestration boundary.
- Core modules may not import `adsk` or `fusion_adapters` at module import time.
  Architecture tests enforce both rules so every core module remains importable
  on the host.

- **MCB-150 — Confirmed intent:** Refactoring shall preserve the requirements in this document except known deviations explicitly selected for correction.
- **MCB-151 — Confirmed intent:** Core parsing and transformation logic should become host-testable without importing or emulating the complete Fusion `adsk` API.
- **MCB-152 — Confirmed intent:** Fusion-specific objects and mutations should remain at adapter boundaries.
- **MCB-153 — Confirmed intent:** Output-file grouping shall have one authoritative representation shared by header, body, tail, filename, and last-operation decisions.
- **MCB-154 — Confirmed intent:** Parser extraction shall preserve streaming behavior by accepting iterables/iterators rather than requiring materialized files.
- **MCB-155 — Confirmed intent:** Refactoring shall preserve processing order and externally observable file contents unless a documented known deviation is deliberately corrected.

## 15. Verification matrix

| Area | Host/source verification | Fusion 360 verification |
|---|---|---|
| Regex and line recognition | Unit tests with strings and generators | Representative post output |
| Header/body/tail boundaries | Streaming `StringIO` and temporary-file tests | Real selected post processor |
| Internal tool-run grouping | Pure operation-metadata tests | Fusion operation selection/order |
| Output-file planning | Pure plan tests for every grouping/setting combination | Actual paths and files generated by add-in |
| Numeric and sequence naming | Pure naming tests and temporary directories | NC Program parameter interaction |
| Rotation mathematics | Vector-adapter/pure-math tests | Machine configuration and safe G-code review |
| Shrink retention | Per-result-file unit tests | Generated operation files containing shrink |
| Rapid restoration | Parser/transformer regression fixtures | G-code visualization and machine-safe review |
| Settings persistence | Fake attribute store tests | Document reopen/reload behavior |
| Error handling | Temporary filesystem failure tests | Fusion dialogs and logging |

### Minimum grouping fixture

Use two setups with the following tool sequence:

```text
Setup A: A1(T1), A2(T1), A3(T2), A4(T1)
Setup B: B1(T3), B2(T3)
```

Each internal operation fixture should contain a unique body marker and one shrink line. Verify with `COMBINE_TOOL` both disabled and enabled.

Expected combined tool runs when enabled:

```text
Setup A: [A1+A2](T1), [A3](T2), [A4](T1)
Setup B: [B1+B2](T3)
```

For every grouping mode, verify:

1. Result-file count and paths.
2. Operation marker membership and order.
3. Exactly one applicable header and tail per result file.
4. Shrink removed from every non-final operation in that file.
5. Shrink retained by the final operation in that file.
6. Streaming processing without complete-file materialization.

## 16. Evidence boundary

This specification is derived from the current repository source, README behavior descriptions, and owner clarifications made during review. The host suite covers the post-processing core, including parsing, writing, grouping, output planning, parameter wrappers, program/setup orchestration, and architecture boundaries. `python3 -m compileall -q commands Tests` and `git diff --check` provide additional syntax and patch-format evidence. Direct `adsk` access is restricted to `fusion_adapters/` and the dialog/UI layer. None of this proves Fusion API compatibility, correct post-processor interaction, UI event behavior, result-file contents, safe machine behavior, or successful execution on a target machine.
