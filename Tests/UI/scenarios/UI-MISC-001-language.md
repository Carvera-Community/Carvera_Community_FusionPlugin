# UI-MISC-001: Language selection

## Steps and assertions

1. Open Misc and record the current language.
2. Select Swedish, close the dialog, and reopen it; confirm the saved selection is Swedish and translated labels are consistently rendered.
3. Select English, close, and reopen; confirm the saved selection and English labels.
4. Confirm neither selection logs a missing-translation warning for the Language tooltip.

## Unresolved assertion

Whether labels must change immediately in the already open dialog is tracked by `UIQ-003`.
