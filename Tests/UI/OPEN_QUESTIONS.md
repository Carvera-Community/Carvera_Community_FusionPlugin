# Open UI acceptance questions

Unresolved expectations are kept here so they do not block unrelated UI
validation. Scenario steps must reference the question ID when an assertion
cannot yet be made.

## UIQ-001: Manual output-folder editing — resolved

Typing a valid path must update the program output folder when the field loses
focus. The browse button remains an alternative way to choose and apply a path.
This behavior is implemented and validated by `UI-OUTPUT-002`.

Related control: `output_folder`.

## UIQ-002: Combine operations availability — resolved

`Combine operations using same tool` must only be enabled when the selected
grouping permits grouping by tool. For the current choices this means `Group on
setup and tool`. This dependency is implemented and validated by
`UI-OUTPUT-003`.

Related controls: `operations_grouping`, `combine_tool`.

## UIQ-003: Language application timing — resolved with future enhancement

The current acceptance requirement is that the language setting is saved and
applied when the dialog is opened again. Immediate relabelling of the open dialog
would be preferable, but Fusion creates the command inputs when the dialog loads
and may not support a reliable live rebuild. Treat immediate application as a
future enhancement rather than a current failure.

Related control: `language`.

## UIQ-004: Rename scope and persistence — resolved

Search and replace keeps its current behavior and renames Fusion setup objects.
With `Only selected Setups` disabled it runs across every setup; with the option
enabled it is limited to the setups currently selected in the Input Selection
tab. The changed names are therefore visible outside the add-in dialog as well.

Related controls: `use_regex`, `find_string`, `replace_string`,
`replace_only_selected`, `replace`.

## Deferred functionality: Tools tab

`ToolsTab` is an intentional future development. It is implemented in source but
is not added to the current dialog layout, so its controls are excluded from the
active UI acceptance inventory. Add its controls and scenarios when the feature
is activated.

## UIQ-005: Invalid regular-expression feedback

Entering an invalid Python regular expression currently leaves the dialog open
and performs no rename, but it gives the user no visible error indication. The
expected feedback mechanism has not been decided: an inline field error, a
message box, or another Fusion-supported notification would all make the
failure understandable.

Related controls: `use_regex`, `find_string`, `replace`.
