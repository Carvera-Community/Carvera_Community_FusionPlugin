# UI-MISC-002: Setup search and replace

## Steps and assertions

1. Record all fixture setup names before testing.
2. Disable Only selected Setups and perform a literal replacement that matches every setup; confirm all matching Fusion setup names change, including unselected setups.
3. Undo or restore the fixture names.
4. In Input Selection, select one eligible setup and deselect the other eligible setups.
5. Enable Only selected Setups, then perform a literal replacement unique to the selected setup's name.
6. Confirm only the matching setup selected in Input Selection changes; unselected matching setups remain unchanged.
7. Enable Python regular expressions and perform a bounded replacement with an unambiguous pattern.
8. Exercise an invalid regular expression and record the UI response without proceeding if Fusion reports an error.
9. Restore the fixture without saving after execution.
