# Open UI acceptance questions

Unresolved expectations are kept here so they do not block unrelated UI
validation. Scenario steps must reference the question ID when an assertion
cannot yet be made.

## UIQ-001: Manual output-folder editing

The output-folder field is editable, but the current UI handler only updates the
program path when the browse button is used. Should typing a valid path into the
field update the program output folder on focus loss, or should the field become
read-only and require the browse button?

Related control: `output_folder`.

## UIQ-002: Combine operations availability

Should `Combine operations using same tool` be enabled for every operations
grouping, or only for groupings where it changes file membership? The current UI
does not express this dependency.

Related controls: `operations_grouping`, `combine_tool`.

## UIQ-003: Language application timing

Should changing Language update the currently open dialog immediately, or only
future dialogs after reopening? The setting is stored, but the intended visible
timing is not specified.

Related control: `language`.

## UIQ-004: Rename scope and persistence

Should Search and replace modify Fusion setup names permanently, only the
add-in's in-memory names for the current run, or both? This must be decided before
asserting the external side effects of the button.

Related controls: `use_regex`, `find_string`, `replace_string`,
`replace_only_selected`, `replace`.

## Deferred functionality: Tools tab

`ToolsTab` is an intentional future development. It is implemented in source but
is not added to the current dialog layout, so its controls are excluded from the
active UI acceptance inventory. Add its controls and scenarios when the feature
is activated.
