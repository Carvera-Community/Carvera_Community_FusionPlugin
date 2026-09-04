# UI-MISC-001: Language selection

## Steps and assertions

1. Open Misc and record the current language.
2. Select Swedish, close the dialog, and reopen it; confirm the saved selection is Swedish and translated labels are consistently rendered.
3. Select English, close, and reopen; confirm the saved selection and English labels.
4. Confirm neither selection logs a missing-translation warning for the Language tooltip.

The bundled translation keys and formatted file-version value are also checked
by `test_language_tooltip_is_complete_in_bundled_languages`. The live step
still confirms that Fusion constructs the tooltip without logging a warning.

Immediate relabelling of the already open dialog is desirable but is not a
current pass condition because Fusion creates the command inputs when the dialog
is loaded.
