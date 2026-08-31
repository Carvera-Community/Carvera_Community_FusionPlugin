# UI-GCODE-003: G-code block anchors

## Steps and assertions

1. Expand G-code Blocks.
2. Enter distinct valid multiline values in Tool change code, ending-sequence codes, and header-end codes.
3. Move focus away from each field, close the dialog, reopen it, and confirm all line breaks and values persist.
4. Restore the defaults: Tool change `M9`, ending sequence `M5`, `M9`, `M30`, and header end `G20`, `G21`.
5. Generate a uniquely named file and confirm processing completes without a parser error.

## Pass condition

Each textbox independently receives and persists multiline text, and restored defaults produce output successfully.
