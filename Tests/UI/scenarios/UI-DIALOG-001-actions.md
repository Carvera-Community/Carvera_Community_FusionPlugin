# UI-DIALOG-001: Dialog actions and persistence

## Steps and assertions

1. Open the dialog without an NC program and confirm Process and Save as default settings are disabled.
2. Select `NCProgram18` and a valid setup; confirm both actions become enabled.
3. Record a harmless default, change it, click Save as default settings, close,
   create a new Fusion document, open the add-in there, and confirm the changed
   default is used. Reopening the same document is not sufficient because its
   document settings may override the default.
4. Confirm Close dismisses the dialog without producing NC output.
5. Confirm Process produces output only when a valid program and at least one error-free setup are selected.
6. Restore the previous harmless setting and save defaults again.

Record the original, changed, newly loaded, and restored values in the result
report.

## Pass condition

Action enablement, cancellation, processing, and default persistence are consistent and no stale duplicate command dialog is created after an add-in reload.
