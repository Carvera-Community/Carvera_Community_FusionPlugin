# UI-OUTPUT-001: Single-file shrink handling

## Preconditions

- Fixture: `Tests/Test 1.f3d`
- NC program: `NCProgram18`
- Post processor: `Makera Carvera Community Post v1.4.6`
- Reload the add-in after source changes.

## Steps

1. Select all compatible setups.
2. Open Output Options and choose Single file.
3. Keep Overwrite existing files and Clear output folder disabled.
4. Enter a unique filename and click Process.
5. Confirm Fusion closes the dialog without a PostDialog error.

## Artifact verification

```sh
python3 Tests/UI/run_ui_tests.py verify UI-OUTPUT-001 "/path/to/generated.cnc"
```

The output must contain exactly one `G92.4 A0 R...`, after an `M9` tail marker and before the single `M30`.
