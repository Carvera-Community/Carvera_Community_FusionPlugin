# Fusion UI acceptance tests

This directory contains the acceptance-test library for the Makera Community
Fusion add-in. These tests are deliberately separate from the host-side pytest
suite: a passing host suite does not prove that Fusion rendered the dialog,
delivered input events, called the Autodesk API, or generated the expected NC
output.

## How the library works

`catalog.json` is the machine-readable index. Every active UI input has a stable
control ID and must reference one or more scenarios. Each scenario has a Markdown
runbook in `scenarios/` with semantic instructions for a human or a Computer Use
agent. Instructions identify controls by their visible labels and values, never
by screen coordinates or transient accessibility indexes.

The runner provides the operational entry point:

```sh
python3 Tests/UI/run_ui_tests.py check
python3 Tests/UI/run_ui_tests.py list
python3 Tests/UI/run_ui_tests.py show UI-OUTPUT-001
python3 Tests/UI/run_ui_tests.py verify UI-OUTPUT-001 /path/to/result.cnc
```

`check` validates the catalog, scenario files, control coverage, and references
to open questions. `verify` runs deterministic checks against artifacts produced
by Fusion. UI actions still run inside Fusion; the repository runner does not
pretend that host-side execution is Fusion acceptance.

## Execution protocol

1. Start Fusion and open the fixture named by the scenario.
2. Reload the Makera Community add-in after source changes. Reopening only the
   command dialog does not reload imported Python modules.
3. Run `show` for the chosen scenario and perform its semantic UI steps.
4. Use a unique output directory or filename. Never enable folder clearing in a
   directory that contains user data.
5. Run the scenario's `verify` command when it produces an artifact.
6. Record the Fusion version, add-in commit, post-processor version, result, and
   artifact path in a temporary test report or the commit/PR evidence. Generated
   NC files and local result reports are not committed.

## Adding a UI input

When adding or changing a dialog control:

1. Add the control to `catalog.json`.
2. Link it to an existing scenario or add a new stable scenario ID and runbook.
3. Add deterministic artifact verification when the behavior has an observable
   file result.
4. If the intended behavior is unknown, add an item to `OPEN_QUESTIONS.md`, set
   the catalog entry's status to `question`, and continue with other scenarios.

The catalog-validation tests ensure that undocumented active controls do not
silently enter the UI.
