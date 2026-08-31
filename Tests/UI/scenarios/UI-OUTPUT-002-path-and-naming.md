# UI-OUTPUT-002: Output path and filename inputs

## Steps and assertions

1. Use the browse button to select a dedicated temporary directory and confirm the displayed path changes.
2. Enter a unique nonnumeric filename with Name must be numeric disabled; confirm Process remains available.
3. Enable Name must be numeric; confirm the nonnumeric filename shows an input error.
4. Enter `0012`; confirm the error clears, sequence-prefix controls become unavailable, and digits derive from the numeric name within the supported bound.
5. Disable numeric naming, enable Prepend sequence number, and exercise digit values 1 through 6.
6. Disable Prepend sequence number and confirm Number of digits becomes disabled.
7. Process one safe case and confirm the result is created in the browsed directory with the expected filename.

## Unresolved assertion

Manual editing of Output folder is tracked by `UIQ-001`; test and record current behavior, but do not classify it as accepted until that question is resolved.
