# UI-GCODE-001: A-axis rotation dependencies

## Steps and assertions

1. Select `NCProgram18`, then open G-code Options.
2. Disable `Rotate A-Axis between setups`; confirm rotated setups become ineligible after accepting the warning, and both Y-retraction controls are disabled.
3. Enable rotation; confirm eligible rotated setups can be selected and `Retract Y on A-axis rotation` becomes enabled.
4. Disable Y retraction; confirm the coordinate input becomes disabled.
5. Enable it and set the coordinate to `-90`; confirm the coordinate remains visible and enabled.
6. Process to a unique file and confirm inserted rotation blocks use `G90 G53 G0 Z-3 Y-90`.

## Safety

Cancel rather than accept any warning whose setup state does not match the fixture described above.
