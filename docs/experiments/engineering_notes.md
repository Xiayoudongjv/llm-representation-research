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

## Shared Extraction Utilities

Added `src/extraction.py` to centralize layer validation, device-safe
tokenized-input handling, and last-token hidden-state extraction. Existing
experiments have not yet been refactored. Future work should migrate EXP-001
through EXP-006 gradually after the shared behavior is validated.

## Shared Plotting Utilities

Added `src/experiment_plots.py` to centralize common matplotlib plotting
patterns for line plots, bar charts, scatter plots, and heatmaps. Existing
experiment scripts have not yet been refactored. Future work should migrate
EXP-005 through EXP-010 plots gradually.
