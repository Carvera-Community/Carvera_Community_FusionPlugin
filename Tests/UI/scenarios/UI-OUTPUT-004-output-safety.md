# UI-OUTPUT-004: Overwrite and clear safety

## Preconditions

Create a dedicated disposable directory containing only test artifacts. Never run this scenario against a user output directory.

## Steps and assertions

1. With Overwrite existing files disabled, generate a file, repeat the same run, and confirm Fusion reports that the file exists without changing it.
2. Enable Overwrite existing files and confirm Clear output folder becomes enabled.
3. Keep Clear disabled, rerun, and confirm only colliding result files are replaced.
4. Put a harmless sentinel file in the disposable directory, enable Clear, process, and confirm the sentinel is removed and expected result files are created.
5. Disable Overwrite and confirm Clear is automatically disabled and unchecked.

## Safety

The clear-folder step is destructive and requires a freshly created, explicitly verified disposable directory.
