# UI-INPUT-001: Program and setup selection

## Preconditions

- Open `Tests/Test 1.f3d` in Fusion Manufacture.
- Reload the add-in and open the Makera Community dialog.

## Steps and assertions

1. Before selecting a program, confirm Process is disabled and the dependent tabs are unavailable.
2. Select `NCProgram18`; confirm Machine is `Carvera 4-axis` and Post Processor is `Makera Carvera Community Post v1.4.6`.
3. Confirm Setup1 is the reference and Process becomes enabled when a valid setup is selected.
4. Toggle the header checkbox off and confirm every enabled setup is deselected and Process becomes disabled.
5. Toggle it on and confirm all eligible setups are selected; rows with Different origin or non-parallel axes remain disabled.
6. Deselect and reselect one eligible setup. Confirm its state and the header checkbox remain consistent.

## Pass condition

Program metadata, setup eligibility, select-all synchronization, and Process enablement follow the steps above without a Fusion error.
