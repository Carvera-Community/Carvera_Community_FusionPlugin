# UI-MISC-002: Setup search and replace

## Current-state exploration

1. Record all fixture setup names before testing.
2. With Only selected Setups enabled, select one eligible setup and perform a literal replacement unique to that name.
3. Confirm only the intended displayed setup name changes.
4. Enable Python regular expressions and perform a bounded replacement with an unambiguous pattern.
5. Exercise an invalid regular expression and record the UI response without proceeding if Fusion reports an error.

## Unresolved assertion

Do not assert persistence or modification of Fusion's source setup names. The intended ownership and persistence are tracked by `UIQ-004`. Restore the fixture without saving after exploratory execution.
