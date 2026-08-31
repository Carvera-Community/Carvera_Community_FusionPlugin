# UI-OUTPUT-002: Output path and filename inputs

## Steps and assertions

1. Type a dedicated temporary directory into Output folder, leave the field, and confirm the program adopts the path by generating the next result there.
2. Use the browse button to select a second dedicated temporary directory and confirm both the displayed and effective paths change.
3. Enter a unique nonnumeric filename with Name must be numeric disabled; confirm Process remains available.
4. Enable Name must be numeric; confirm the nonnumeric filename shows an input error.
5. Enter `0012`; confirm the error clears, sequence-prefix controls become unavailable, and digits derive from the numeric name within the supported bound.
6. Disable numeric naming, enable Prepend sequence number, and exercise digit values 1 through 6.
7. Disable Prepend sequence number and confirm Number of digits becomes disabled.
8. Process one safe case and confirm the result is created in the selected directory with the expected filename.

Record both temporary paths in the result report. The second path must come
from the native folder picker; typing it into the text field does not cover the
browse button.
