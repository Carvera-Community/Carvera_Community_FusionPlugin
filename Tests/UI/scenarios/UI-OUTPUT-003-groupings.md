# UI-OUTPUT-003: Operations grouping choices

## Steps and assertions

Using a dedicated empty output directory, process the fixture once for each choice:

1. Single file: one file contains all selected content.
2. Group on setup: one file is produced per populated setup.
3. Group on setup and tool: one file is produced per consecutive tool run within each setup.
4. None, one file per operation: one file is produced per internal operation group.
5. Repeat representative cases with Flat file structure disabled and enabled; confirm only path layout changes, not membership.

## Unresolved assertion

Exercise Combine operations using same tool and record the observed files. Its exact enablement and interaction with all grouping choices is tracked by `UIQ-002`.
