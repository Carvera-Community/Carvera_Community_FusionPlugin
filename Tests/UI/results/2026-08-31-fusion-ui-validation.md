# Fusion UI acceptance result

- Scenario: Full UI catalog pass
- Date: 2026-08-31
- Tester: Codex with user-provided Fusion fixture
- Fusion version: Not recorded
- Add-in commit: Working tree on `refactoring-testability`
- Post-processor version: Community Post v1.4.6
- Fixture: Test model with NCProgram18; Setup1 and Setup2
- Output artifact: `~/NC Programs/ui-validation-shrink-tail-reloaded.cnc`
- Result: PARTIAL

## Observations

- `UI-INPUT-001`: PASS. Select-all follows the eligible setup rows in both
  directions; disabled rows remain unavailable and Process follows selection.
- `UI-GCODE-001`: PARTIAL. Rotation warning, rotated-setup deselection, and
  safe-Y dependencies behaved as specified. Exact `Y-90` output was not
  inspected in the generated artifact during this pass.
- `UI-GCODE-002`: PARTIAL. Rapid restoration controls enabled and disabled
  their dependent distance input as specified. The complete `3`/`10` and
  `0 mm`/`50 mm` boundary set and reopened `3`/`20 mm` values were not all
  recorded during this pass.
- `UI-GCODE-003`: PASS. Distinct multiline values persisted across dialog
  reopen, the recorded original values were restored, and
  `ui-gcode-blocks-20260831.cnc` was generated without a parser error.
- `UI-OUTPUT-001`: PASS. The generated artifact contains one shrink command in
  the tail and one `M30`.
- `UI-OUTPUT-002`: PARTIAL. A manually entered output folder was applied
  on focus loss and produced
  `/tmp/makera-ui-output.S9BGlV/manual-folder-validation.cnc`. Numeric-name
  validation blocks a nonnumeric name, derives five digits from `00123`, and
  disables sequence-prefix controls. The sequence digit limits 1 and 6 and the
  prepend dependency were also exercised. The native folder-picker path was
  not completed reliably by the UI automation during this pass.
- `UI-OUTPUT-003`: PASS. The fixture generated 1 Single file, 7 Setup files,
  12 combined Setup-and-Tool files, and 14 Per Operation files. The non-flat
  Per Operation run generated the same 14 basenames with byte-identical content
  under setup directories. Combine is only available for Setup and Tool and is
  cleared on departure.
- `UI-OUTPUT-004`: PASS. Existing-file protection produced the expected error,
  overwrite replaced the colliding result, and the confirmed clear run removed
  a disposable sentinel before recreating only `safety.cnc`. Disabling
  overwrite disabled and cleared the clear-folder option.
- `UI-MISC-001`: PARTIAL for language selection, persistence, and compact Swedish
  tab labels. The translation-version key is covered by host tests; the UI
  automation API does not provide a pointer-hover action for tooltip rendering.
  Bundled tooltip keys and file-version formatting are now host-tested, but a
  live Fusion-log observation remains outstanding.
- `UI-MISC-002`: PASS. All-setup and selected-only literal
  renaming passed. A bounded selected-only regex renamed `Setup1` to `Regex1`
  and was restored. After implementing the resolved `UIQ-005` requirement, an
  invalid `[` expression displayed Fusion's red inline error indicator when
  focus left the field, and Search and replace left `Setup1` unchanged.
- `UI-DIALOG-001`: PARTIAL. Process enablement, Close without output, Process with
  output, document persistence, and Save as default were exercised. The
  default file changed to the harmless test value and was restored to its
  recorded original value. Loading the changed default in a newly created
  Fusion document was not observed during this pass.

Fusion's Add-Ins off/on switch does not reload already imported Python modules;
the final pass was therefore performed after a full Fusion restart.

## Automated verification

```text
UI catalog valid: 11 scenarios, 32 active controls
204 passed
Total coverage: 92%
git diff --check: clean
```

## Open questions or failures

- Complete the native-folder-picker result and verify the resulting effective path.
- Generate and run the `UI-GCODE-001` artifact verifier against exact `Y-90` output.
- Record all rapid-input boundaries and reopened persistence values.
- Observe the Fusion log while constructing both Language tooltips.
- Verify a changed default in a newly created Fusion document, then restore it.
