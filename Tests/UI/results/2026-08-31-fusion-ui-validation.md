# Fusion UI acceptance result

- Scenario: Full UI catalog pass
- Date: 2026-08-31
- Tester: Codex with user-provided Fusion fixture
- Fusion version: Not recorded
- Add-in commit: Working tree on `refactoring-testability`
- Post-processor version: Community Post v1.4.6
- Fixture: Test model with NCProgram18; Setup1 and Setup2
- Output artifact: `/Users/moinois/NC Programs/ui-validation-shrink-tail-reloaded.cnc`
- Result: PASS

## Observations

- `UI-INPUT-001`: PASS. Select-all follows the eligible setup rows in both
  directions; disabled rows remain unavailable and Process follows selection.
- `UI-GCODE-001`: PASS. Rotation warning, rotated-setup deselection, and safe-Y
  dependencies behaved as specified.
- `UI-GCODE-002`: PASS. Rapid restoration controls enabled and disabled their
  dependent distance input as specified.
- `UI-GCODE-003`: PASS. Distinct multiline values persisted across dialog
  reopen, the recorded original values were restored, and
  `ui-gcode-blocks-20260831.cnc` was generated without a parser error.
- `UI-OUTPUT-001`: PASS. The generated artifact contains one shrink command in
  the tail and one `M30`.
- `UI-OUTPUT-002`: PASS. A manually entered output folder was applied
  on focus loss and produced
  `/tmp/makera-ui-output.S9BGlV/manual-folder-validation.cnc`. Numeric-name
  validation blocks a nonnumeric name, derives five digits from `00123`, and
  disables sequence-prefix controls. The sequence digit limits 1 and 6 and the
  prepend dependency were also exercised.
- `UI-OUTPUT-003`: PASS. The fixture generated 1 Single file, 7 Setup files,
  12 combined Setup-and-Tool files, and 14 Per Operation files. The non-flat
  Per Operation run generated the same 14 basenames with byte-identical content
  under setup directories. Combine is only available for Setup and Tool and is
  cleared on departure.
- `UI-OUTPUT-004`: PASS. Existing-file protection produced the expected error,
  overwrite replaced the colliding result, and the confirmed clear run removed
  a disposable sentinel before recreating only `safety.cnc`. Disabling
  overwrite disabled and cleared the clear-folder option.
- `UI-MISC-001`: PASS for language selection, persistence, and compact Swedish
  tab labels. The translation-version key is covered by host tests; the UI
  automation API does not provide a pointer-hover action for tooltip rendering.
- `UI-MISC-002`: PASS. All-setup and selected-only literal
  renaming passed. A bounded selected-only regex renamed `Setup1` to `Regex1`
  and was restored. After implementing the resolved `UIQ-005` requirement, an
  invalid `[` expression displayed Fusion's red inline error indicator when
  focus left the field, and Search and replace left `Setup1` unchanged.
- `UI-DIALOG-001`: PASS. Process enablement, Close without output, Process with
  output, document persistence, and Save as default were exercised. The
  default file changed to the harmless test value and was restored to its
  recorded original value; default-loading logic is additionally host-tested.

Fusion's Add-Ins off/on switch does not reload already imported Python modules;
the final pass was therefore performed after a full Fusion restart.

## Automated verification

```text
UI catalog valid: 11 scenarios, 32 active controls
201 passed
Total coverage: 92%
git diff --check: clean
```

## Open questions or failures

None from this acceptance pass.
