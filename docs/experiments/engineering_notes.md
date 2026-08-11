# Engineering Notes

## Why IO Utilities Were Added

The experiment scripts contained repeated CSV and JSON loading and writing
logic. Repeated schema definitions create a risk that CSV headers and rows
become misaligned. This risk was exposed by the EXP-006 CSV issue discovered
during later analysis.

## Current Scope

- shared UTF-8 IO helpers
- CSV schema validation
- basic local tests
- no experiment refactor yet

The utilities are infrastructure only and do not change existing experiment
outputs.

## Future Refactor Plan

1. Migrate experiment scripts gradually to `src/experiment_io.py`.
2. Add shared representation extraction utilities.
3. Unify plotting utilities.
4. Add smoke tests.
5. Standardize CSV schemas.
