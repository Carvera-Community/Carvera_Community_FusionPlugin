# UI-GCODE-002: Rapid restoration inputs

## Steps and assertions

1. Open G-code Options with `NCProgram18` selected.
2. Disable Restore rapid moves and confirm Minimum rapid move distance is disabled.
3. Enable Restore rapid moves and confirm Minimum rapid move distance is enabled.
4. Exercise the minimum values and maximum values exposed by both numeric controls.
5. Set Max steps to `3` and Minimum distance to `20 mm`, close and reopen the dialog, and confirm the values persist for the document.

## Artifact boundary

Whether a particular toolpath qualifies for a restored rapid is covered by host tests. This scenario validates Fusion input delivery, ranges, dependencies, and persistence.
