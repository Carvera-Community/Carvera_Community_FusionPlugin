# Code Review TODO

This document records potential bugs and logical gaps found during a source review of the repository. The findings are ordered by recommended priority. No target-side Fusion 360 validation has been performed yet.

## 1. Parse decimal G-codes in `_BODY_RE`

- **Status:** Handled in the current working tree
- **Priority:** Critical
- **Location:** [`commands/postProcessor/line.py`](commands/postProcessor/line.py#L13)
- **Related flow:** [`commands/postProcessor/operations/operation/parser.py`](commands/postProcessor/operations/operation/parser.py#L84)

### Problem

`_BODY_RE` previously accepted only integer G-codes:

```python
r"(G(?P<G>[0-9]+) *)?"
```

For `G92.4 A0 R0`, the `G` group therefore contained `92`, while the remaining `.4 A0 R0` was consumed by the unrestricted end of the expression. Consequently, the `gCode == 92.4` branch in the operation parser was never reached and the shrink line was not registered.

### Implemented adjustment

The expression now allows an optional decimal part:

```python
r"(G(?P<G>[0-9]+(?:\.[0-9]*)?) *)?"
```

Regression tests should still verify at least `G0`, `G1`, `G92.4`, and numbered variants such as `N10 G92.4 A0 R0`.

## 2. Write operation bodies for every grouping mode

- **Status:** Implemented in the current working tree; awaiting Fusion 360 verification
- **Priority:** Critical
- **Current implementation:** [`commands/postProcessor/output_plan.py`](commands/postProcessor/output_plan.py), [`commands/postProcessor/output_renderer.py`](commands/postProcessor/output_renderer.py)

### Problem

The output file is opened for every operation, but `operation.WriteBody()` is called only for `SINGLE_FILE` and `SETUP` grouping:

```python
with pathToOpen.open(FileModes.APPEND) as fileHandle:
    if Settings(Settings.OPERATIONS_GROUPING) in [
        Settings.OperationsGroupings.SINGLE_FILE,
        Settings.OperationsGroupings.SETUP,
    ]:
        operation.WriteBody(fileHandle)
```

For `SETUP_AND_TOOL` and `PER_OPERATION`, the generated files can therefore receive headers and tails without an operation body.

### Implemented adjustment

Write the body after the grouping-dependent filename has been resolved:

```python
with pathToOpen.open(FileModes.APPEND) as fileHandle:
    operation.WriteBody(fileHandle)
```

The grouping guard has been removed, so every internal operation body is now written to its resolved result file. Validate all four grouping modes and confirm the resulting file boundaries, headers, bodies, and tails.

## 3. Fix invalid `Setup` access during numeric tail writing

- **Status:** Implemented in the current working tree; awaiting Fusion 360 verification
- **Priority:** Critical
- **Current implementation:** [`commands/postProcessor/output_plan.py`](commands/postProcessor/output_plan.py)
- **Historical location:** `commands/postProcessor/setups/tail_writer.py` (removed)

### Problem

The numeric naming branch calls members that do not exist on `Setup`:

```python
setup.SetFileName(fileName)
fileName = setup._operations.fileName
```

`Setup` has no `SetFileName()` method and no `_operations` attribute. This should raise `AttributeError` when numeric naming is used outside `SINGLE_FILE` mode.

### Implemented adjustment

Use the setup context and handle a missing operations collection explicitly:

```python
if Settings(Settings.NUMERIC_NAME) and fileName is not None:
    setup.ctx.SetFileName(fileName)

setup.WriteTail()

if Settings(Settings.NUMERIC_NAME) and setup.ctx.operations is not None:
    fileName = setup.ctx.operations.fileName
```

Verify numeric naming with `SETUP`, `SETUP_AND_TOOL`, and `PER_OPERATION` grouping.

## 4. Initialize the fallback result in `machineHasAAxis`

- **Status:** Implemented in the current working tree; awaiting Fusion 360 verification
- **Priority:** High
- **Location:** [`commands/postProcessor/program.py`](commands/postProcessor/program.py#L89)

### Problem

`machineHasAAxis` returns `unreadable_extra_axis` after inspecting all axes, but that variable is assigned only when a particular `RuntimeError` is caught. A normal machine with no rotary axis and no exception reaches the return with an uninitialized local variable, causing `UnboundLocalError`.

### Implemented adjustment

Initialize the value before the loop:

```python
unreadable_extra_axis = False

for index in range(axes.count):
    # Existing axis inspection.
```

Add coverage for a machine without a rotary axis, a machine with a readable rotary axis, and the known unreadable-extra-axis case. Also document whether an unreadable extra axis should conservatively return `True`.

## 5. Replace bitwise OR in rapid-move settings

- **Status:** Implemented in the current working tree; awaiting Fusion 360 verification
- **Priority:** High
- **Location:** [`commands/postProcessor/operations/operation/parser.py`](commands/postProcessor/operations/operation/parser.py#L120)

### Problem

The rapid parser combines configured integers with defaults using bitwise OR:

```python
minDist = Settings(Settings.RAPID_MOVES_MINIMUM_DISTANCE) | 20
maxStepsInbetween = Settings(Settings.RAPID_MOVES_MAX_STEPS) | 3
```

This changes valid configured values. For example, `5 | 20` produces `21`, and `4 | 3` produces `7`.

### Implemented adjustment

Use the configured value unless it is absent:

```python
minDist = Settings(Settings.RAPID_MOVES_MINIMUM_DISTANCE)
if minDist is None:
    minDist = 20

maxStepsInbetween = Settings(Settings.RAPID_MOVES_MAX_STEPS)
if maxStepsInbetween is None:
    maxStepsInbetween = 3
```

If zero is invalid, validate it explicitly instead of relying on truthiness. Add tests showing that configured values reach `RapidsParser` unchanged.

## 6. Preserve shrink on the last operation in each result file

- **Status:** Implemented in the current working tree; awaiting Fusion 360 verification
- **Priority:** High
- **Location:** [`commands/postProcessor/setups/setups_context.py`](commands/postProcessor/setups/setups_context.py#L39)
- **Related filtering:** [`commands/postProcessor/setups/setup/setup.py`](commands/postProcessor/setups/setup/setup.py#L209)
- **Related output routing:** [`commands/postProcessor/output_plan.py`](commands/postProcessor/output_plan.py), [`commands/postProcessor/output_renderer.py`](commands/postProcessor/output_renderer.py)

### Problem

The current implementation assigns one global `isLastOp` flag based on the last selected setup:

```python
lastSetup = self.selected[-1]
```

This does not represent the output contract. The last operation in each generated result file must retain its shrink line if it has one. The required behavior depends on grouping:

- `SINGLE_FILE`: only the final operation in the single result file retains shrink.
- `SETUP`: the final operation in each setup file retains shrink.
- `SETUP_AND_TOOL`: the final operation in each consecutive tool-run file retains shrink.
- `PER_OPERATION`: every result file contains one internal operation, so each operation retains shrink.

The current global flag also fails when the last selected setup produces no operations, because no earlier operation is then marked as final.

### Implemented adjustment

Final-operation status is now assigned during output writing from the active grouping rather than during input parsing:

1. `SINGLE_FILE` marks only the final body operation across all non-empty setups.
2. `SETUP` marks the final body operation in each non-empty setup.
3. `SETUP_AND_TOOL` and `PER_OPERATION` mark each internal operation group because each group has its own result file.
4. All flags are reset before they are reassigned, preventing stale state between output runs.

The old `isLastSetup` parse parameter and input-order assignment have been removed. Fusion 360 validation must confirm that filename routing and the final-operation decisions remain aligned in every grouping mode.

## 7. Track every shrink line in an operation

- **Status:** Closed — not applicable; the input contract guarantees at most one shrink line per operation
- **Priority:** Medium
- **Locations:**
  - [`commands/postProcessor/operations/operation/operation_context.py`](commands/postProcessor/operations/operation/operation_context.py#L28)
  - [`commands/postProcessor/operations/operation/parser.py`](commands/postProcessor/operations/operation/parser.py#L102)
  - [`commands/postProcessor/operations/operation/body_writer.py`](commands/postProcessor/operations/operation/body_writer.py#L45)

### Problem

The context stores one `shrinkLine`, and the parser stops recording after the first match:

```python
if not ctx.hasShrink:
    ctx.shrinkLine = lineNumber
```

This would be a problem if an operation could contain multiple matching lines. The postprocessor contract has now been clarified: an operation contains at most one shrink line. A single `shrinkLine` is therefore sufficient.

### Proposed adjustment

No collection change is required while the one-shrink-per-operation invariant holds. Document that invariant and add a regression test for it.

If the input contract changes in the future, track all matching line numbers:

```python
shrinkLines: set[int] = field(default_factory=set)
```

During parsing:

```python
ctx.shrinkLines.add(lineNumber)
```

During writing:

```python
if (
    float(gCode) == 92.4
    and float(aCode) == 0.0
    and lineMatch.group("R") is not None
    and not ctx.isLastOp
):
    return row in ctx.shrinkLines
```

The current implementation remains valid only while the documented invariant is maintained.

## 8. Use value comparison for `subOperationIndexWithTool`

- **Status:** Implemented in the current working tree; awaiting Fusion 360 verification
- **Priority:** Low
- **Location:** [`commands/postProcessor/operations/operation/operation.py`](commands/postProcessor/operations/operation/operation.py#L71)

### Problem

The code uses object identity to compare an integer with `-1`:

```python
self.ctx.subOperationIndexWithTool is not -1
```

Integer interning can make this appear to work, but `is` is not a value comparison and should not be relied upon here.

### Implemented adjustment

Use numeric value comparison:

```python
self.ctx.subOperationIndexWithTool != -1
```

## 9. Add automated regression tests

- **Status:** Handled — 177 host tests pass with 90% statement coverage; Fusion 360 acceptance testing remains
- **Priority:** High
- **Scope:** Repository-wide

### Problem

No automated test files or configured test suite were found. The repository depends on Fusion 360's `adsk` API, but much of the parsing, grouping, filename progression, and output filtering can still be tested with lightweight fakes or extracted pure functions.

### Proposed adjustment

Add host-side regression tests covering:

- Integer and decimal G-code parsing, including optional line numbers.
- Presence and absence of A and R parameters.
- Removal of shrink lines from all non-final output operations.
- Empty and fully suppressed setups.
- All grouping modes.
- Numeric filename progression across setup headers, bodies, and tails.
- Machines with no rotary axis, a readable rotary axis, and unreadable extra axes.
- Rapid-move settings passing through unchanged.

Keep host/source verification distinct from validation inside Fusion 360.

### Current coverage

- Decimal G-code and A/R parameter recognition.
- Leading line-number removal and feed removal outside comments.
- Rapid-line parsing, streaming file segmentation, step-limit validation, and effective-distance analysis.
- Session-only safety-setting serialization and legacy-value reset.

Output planning, header/body/tail assembly, rotation injection, shrink retention per result file, filename routing, settings, and Fusion adapter boundaries are now covered on the host. A streaming end-to-end fixture renders all four grouping modes. Fusion API interaction, UI rendering, and machine-safe acceptance still require Fusion 360.

## 10. Correct the inverted shrink-line removal condition

- **Status:** Implemented in the current working tree; awaiting Fusion 360 verification
- **Priority:** Critical
- **Location:** [`commands/postProcessor/operations/operation/body_writer.py`](commands/postProcessor/operations/operation/body_writer.py#L45)
- **Specification:** [`spec/current-behavior.md`](spec/current-behavior.md), `MCB-D01`

### Problem

`_matchLine()` returns whether the caller should skip the current line. The shrink branch currently returns:

```python
return row != ctx.shrinkLine
```

For the registered shrink row, the expression is false, so the caller writes the row. For any other matching shrink row, the expression is true and the caller skips it. Because the input contract allows at most one shrink row per operation, the current condition retains the shrink in a non-final operation instead of removing it.

### Implemented adjustment

Skip the registered shrink row when the operation is not final in its result file:

```python
return row == ctx.shrinkLine
```

Add regression tests covering shrink retention and removal for all four output grouping modes. Keep the operation when it has no shrink, and preserve the shrink on the final operation in each result file.

## 11. Align safety-setting persistence with the documented contract

- **Status:** Implemented in the current working tree; awaiting Fusion 360 verification
- **Priority:** High
- **Location:** [`commands/postProcessor/settings/settings.py`](commands/postProcessor/settings/settings.py#L125)
- **Related UI:** [`commands/postProcessor/dialog/layout/output_tab.py`](commands/postProcessor/dialog/layout/output_tab.py#L218)
- **Specification:** [`spec/current-behavior.md`](spec/current-behavior.md), `MCB-D09`

### Problem

The README states that `Overwrite existing files` and `Clear output folder` are not saved because they are safety-sensitive choices. The current event handlers store both values in the shared settings dictionary, and `Settings.Save()` serializes that complete dictionary to the active document.

### Implemented adjustment

Both values are now excluded from document and local-default serialization and reset to `False` whenever settings are loaded. Add document reload tests and verify the corresponding Fusion dialog state.

## 12. Reuse the first detected tail safely in every output mode

- **Status:** Implemented in the current working tree; awaiting Fusion 360 verification
- **Priority:** High
- **Locations:**
  - [`commands/postProcessor/output_plan.py`](commands/postProcessor/output_plan.py)
  - [`commands/postProcessor/output_renderer.py`](commands/postProcessor/output_renderer.py)
  - [`commands/postProcessor/operations/operation/tail_writer.py`](commands/postProcessor/operations/operation/tail_writer.py)
- **Specification:** [`spec/current-behavior.md`](spec/current-behavior.md), `MCB-D10`

### Problem

The confirmed contract is to reuse the first detected tail. `SINGLE_FILE` chooses the setup that initiates tail writing by `hasHeader`, while granular modes call `WriteTail()` on every internal operation. If an operation has no detected tail, `tailStartLine == -1` causes its complete temporary file to satisfy `row >= tailStartLine` and potentially be appended as tail content.

### Implemented adjustment

`SINGLE_FILE` now selects the first setup with a detected tail rather than the first setup with a header. Granular modes reuse `operationWithTail`, the first detected tail in the setup, for every result file. An operation whose `tailStartLine` is negative is no longer selected as a tail source. Add fixtures where only the first operation contains a tail and where the first header-bearing operation differs from the first tail-bearing operation.

## 13. Use XY travel in rapid-move effective distance

- **Status:** Implemented in the current working tree; covered by a host regression test
- **Priority:** High
- **Location:** [`commands/postProcessor/operations/operation/rapidsParser.py`](commands/postProcessor/operations/operation/rapidsParser.py#L512)
- **Specification:** [`spec/current-behavior.md`](spec/current-behavior.md), `MCB-D11`

### Problem

`getEffectiveLength()` documented the effective distance as the greater of total XY travel and combined Z travel, but returned `zDist + zDist`. Long XY moves could therefore be rejected when their doubled Z travel was below the configured minimum.

### Implemented adjustment

The calculation now follows the documented rule:

```python
return max(self.totalXYDistance, zDist)
```

The host suite includes a fixture with 30 mm XY travel, 10 mm combined Z travel, and a 25 mm threshold.

## 14. Group consecutive equal-tool operations for `SETUP_AND_TOOL`

- **Status:** Implemented; covered by planner and complete-output host tests; awaiting Fusion 360 verification
- **Priority:** Critical
- **Location:** [`commands/postProcessor/output_plan.py`](commands/postProcessor/output_plan.py)

### Problem

The first complete result-file planner treated `SETUP_AND_TOOL` like `PER_OPERATION`, producing one file for every internal operation even when adjacent operations used the same tool.

### Implemented adjustment

The planner now forms consecutive tool runs. For `T1, T1, T2, T1`, output membership is `(T1, T1)`, `(T2)`, `(T1)`, and the repeated final T1 run receives the existing `_2` filename suffix.

## 15. Scan through multi-line headers before writing the body

- **Status:** Implemented; covered by a complete-output host regression test; awaiting Fusion 360 verification
- **Priority:** Critical
- **Location:** [`commands/postProcessor/operations/operation/body_writer.py`](commands/postProcessor/operations/operation/body_writer.py)

### Problem

The streaming body loop stopped whenever the next row was outside the body range, including while it was still scanning header rows. A body beginning after row 1 could therefore be omitted completely.

### Implemented adjustment

The writer now scans until `body.start` and only applies the stop condition after reaching the body range. It still streams the source file and stops immediately after `body.stop`.

## Current verification status

- `python3 -m compileall -q commands Tests` passes.
- `python3 -m pytest -q` passes 177 tests with 90% statement coverage.
- Complete streaming output fixtures cover all four grouping modes, ordered body membership, shrink retention, and one tail per result file.
- No Fusion 360 runtime validation has been performed.
- `git diff --check` passes.
