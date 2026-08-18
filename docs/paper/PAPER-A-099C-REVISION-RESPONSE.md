# Paper-A 099C Revision Response

This document records how Task-099C addressed the Task-099B adversarial
review. It is a manuscript-revision response, not new scientific authority.

## Entry Identity

- Pre-revision HEAD: `370cbc322487de45046854b5f4b62df1af945b32`
- Revised manuscript: `docs/paper/PAPER-A-FIRST-FULL-DRAFT.md`
- Revision type: manuscript-only / supporting-asset revision
- New experiment designed: `false`
- New experiment run: `false`

## Issue-Resolution Matrix

### Major Issues

| Issue ID | Severity | Reviewer concern | Affected section | Repair class | Revision made | Manuscript location | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | MAJOR | Central claim's "under multiple held-out conditions" blurred formal and descriptive support | Abstract, Introduction | CLAIM_NARROWING | Locked a bounded central claim that distinguishes tested-condition recovery from heterogeneity and the unsupported predictor | Abstract, Introduction Section 1 | RESOLVED |
| M2 | MAJOR | Top prior works and critical citations remained TODO/unverified | Related Work, References | REFERENCE_POSITIONING | Replaced TODO anchors with the 099B-0 prior-art inventory and added explicit references 1-11; final primary-source verification remains pending for one generic steering citation and final bibliography | Related Work, References | PARTIALLY_RESOLVED |
| M3 | MAJOR | Main figures were absent; EXP-023 heterogeneity and EXP-024 all-10 scatter not visible | Figures and tables | FIGURE_TABLE_ONLY | Added evidence-summary table in Methods and updated figure plan with explicit required captions/panels; actual figure production remains for the next production step | Methods 3.7, Figure and Table Placement Notes | PARTIALLY_RESOLVED |
| M4 | MAJOR | Abstract/Introduction gap overgeneralized prior-work assumptions | Abstract, Introduction | MANUSCRIPT_ONLY | Rewrote Abstract and Introduction to make prior-art awareness explicit and to avoid "first/assumes stable/unlike all previous work" framing | Abstract, Introduction | RESOLVED |
| M5 | MAJOR | Dataset sizes, class mapping, optimization/seed, tie handling, and data/code availability underspecified | Methods | METHODS_REPRODUCIBILITY | Added record/source-family counts, class mapping, local-only model/tokenizer semantics, frozen seed statement, tie/permutation framing, and evidence summary table | Methods Sections 3.1-3.7 | RESOLVED |

### Minor Issues

| Issue ID | Severity | Reviewer concern | Revision made | Status |
| --- | --- | --- | --- | --- |
| m1 | MINOR | Conclusion said "often recover" without formal frequency support | Removed "often"; conclusion now uses "in multiple tested conditions" and "heterogeneous" | RESOLVED |
| m2 | MINOR | Results remained partly experiment-log-like | Restructured Results around scientific questions with experiment IDs inside the argument | RESOLVED |
| m3 | MINOR | EXP-021 qualification scope could be repeated near fixed-readout degradation claims | Added explicit qualification-scope language in Results 4.3 | RESOLVED |
| m4 | MINOR | Introduction geometry/information-content motivation needed to be marked as framing | Rewrote Introduction to make the measurement framing explicit | RESOLVED |

## Revision Self-Audit

- `MAJOR_RESOLVED_COUNT = 3`
- `MAJOR_PARTIALLY_RESOLVED_COUNT = 2`
- `MAJOR_UNRESOLVED_COUNT = 0`
- `MINOR_RESOLVED_COUNT = 4`

The two partially resolved major issues are production/reference-verification
tasks, not scientific blockers. They require figure/table production and final
primary-source bibliography verification rather than a new experiment.

## Required Flags

- `PAPER_A_099C_MANUSCRIPT_REVISION_COMPLETE = true`
- `PAPER_A_099C_CORE_CLAIM_NARROWED = true`
- `PAPER_A_099C_NOVELTY_REPOSITIONED = true`
- `PAPER_A_099C_EXP023_NO_REPLICATION_CLEAR = true`
- `PAPER_A_099C_EXP024_PRIMARY_NOT_SUPPORTED_CLEAR = true`
- `PAPER_A_099C_BEHAVIORAL_BOUNDARY_CLEAR = true`
- `PAPER_A_099C_TUNED_LENS_POSITIONING_CLEAR = true`
- `PAPER_A_099C_MODEL_STITCHING_POSITIONING_CLEAR = true`
- `PAPER_A_099C_PRIMARY_N_10_CLEAR = true`
- `PAPER_A_099C_PANEL_BOUNDED_LANGUAGE_CLEAR = true`
- `PAPER_A_099C_TRANSPORT_OVERCLAIM = false`
- `PAPER_A_099C_FUNCTIONAL_OVERCLAIM = false`
- `PAPER_A_099C_MAJOR_ISSUES_RESOLVED = 3`
- `PAPER_A_099C_MAJOR_ISSUES_PARTIAL = 2`
- `PAPER_A_099C_MAJOR_ISSUES_UNRESOLVED = 0`
- `PAPER_A_099C_NEW_EXPERIMENT_DESIGNED = false`
- `PAPER_A_099C_NEW_EXPERIMENT_REQUIRED_FOR_CORE_CLAIM = false`
- `PAPER_A_099C_SUBMISSION_READY = false`
- `PAPER_A_099C_NEXT_HIGHEST_PRIORITY_GAP = actual production of the EXP-023 heterogeneity and EXP-024 all-10-condition scatter figures`

Task 099C stops here. The experiment line remains closed.
