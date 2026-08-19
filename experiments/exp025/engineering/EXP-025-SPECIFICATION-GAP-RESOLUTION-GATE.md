# EXP-025 Specification Gap Resolution Gate

Task: `100D-E0`

Classification: `SPECIFICATION_GOVERNANCE_GATE_ONLY`

This gate evaluates the six specification gaps recorded by Task 100D-D before
any formal-executor implementation. It does not modify `run_exp025.py`, does not
create a recovery authorization, and does not access DIAGNOSTIC or EVAL
outcomes.

## Entry Gate

```text
EXP025_100D_E0_REPOSITORY_HEAD = 6befa7a1b7ec39fef5a0119a572495b1e9e5b3f7
HEAD == origin/main = true
TRACKED_TREE_CLEAN = true
STAGING_EMPTY = true
```

Known pre-existing untracked authorization/forensic artifacts remain allowed and
untouched.

## Gap Resolution Table

| GAP_ID | MISSING_RULE | SCIENTIFIC_ENDPOINT_AFFECTED | CURRENT_AUTHORITY | POTENTIAL_EFFECT_ON_RESULT | RESOLUTION_STATUS |
| --- | --- | --- | --- | --- | --- |
| `GAP-001` | Spearman tie-handling for secondary RQ3 | Secondary `rho_secondary` and exact permutation p-value | `EXP-025-PREREGISTRATION.md`, Secondary RQ3 Analysis; `EXP-024-PREREGISTRATION.md`, Primary Statistic | Average-rank vs other tie handling can change `rho`, permutation p, and secondary support classification | `UNRESOLVED_D` |
| `GAP-002` | Exact permutation tie/zero p-value counting convention | Secondary exact permutation p-value and support classification | `EXP-025-PREREGISTRATION.md`, Secondary RQ3 Analysis; `EXP-024-PREREGISTRATION.md`, Primary Exact Test | `>=` vs `>`, tie inclusion, and zero-`rho` handling can change the exact p-value | `UNRESOLVED_D` |
| `GAP-003` | Canonical JSON schema, numeric serialization precision, key order, newline, and pre-publication hashing | Result publication/provenance only | `CANONICAL-RESULT-RETENTION.md`; existing atomic JSON convention in `run_exp022a.py` and EXP-022A runner preflight | Does not change fitted parameters, representations, statistics, classification, p-values, routing, or scientific interpretation | `RESOLVED_C` |
| `GAP-004` | Zero-variance/near-zero scale behavior for `A_sigma` and `A_mu_sigma` | Calibration variants `A_sigma`/`A_mu_sigma`, EVAL balanced accuracy, `G_eval`, routing | `EXP-025-PREREGISTRATION.md`; `EXP-024-PREREGISTRATION.md`, calibration definitions | Different zero-scale handling can change calibration inputs, BA, `G_eval`, and routing | `UNRESOLVED_D` |
| `GAP-005` | Effective sample size zero for D/G exact binomial rule | D/G binomial p-values and D+/D-/G+/G- classification | `EXP-025-PREREGISTRATION.md`, D/G Inference Rules | `effective_n=0` leaves the binomial formula undefined and can change gate classification | `UNRESOLVED_D` |
| `GAP-006` | Exact multi-class balanced-accuracy aggregation definition | `S_diag`, `G_eval`, measurement qualification floor, routing | `EXP-025-PREREGISTRATION.md`; `EXP-024-PREREGISTRATION.md`; current code helpers are not frozen scientific authority | Different balanced-accuracy aggregation can change BA, `S_diag`, `G_eval`, and routing | `UNRESOLVED_D` |

## Classification Summary

```text
RESOLVED_A = 0
RESOLVED_B = 0
RESOLVED_C = 1
UNRESOLVED_D = 5
AMBIGUOUS_E = 0
```

## Authority-Ordered Reasoning

### GAP-003: RESOLVED_C

The canonical JSON serialization/provenance detail is resolved from pre-existing
engineering serialization conventions, not from any scientific choice:

- `experiments/exp022a/run_exp022a.py`, `atomic_write_json`:
  `json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)`
  followed by a trailing newline;
- `docs/experiments/EXP-022A-RUNNER-PREFLIGHT.md`, "Known non-scientific
  implementation choices": UTF-8, two-space indentation, sorted keys, and
  staging-derived temporary publication files;
- `docs/research/CANONICAL-RESULT-RETENTION.md`: canonical result identity,
  provenance, SHA-256, and version-control content rules.

This resolution cannot change any fitted parameter, representation, statistic,
classification, p-value, routing outcome, or scientific interpretation.

### GAP-001, GAP-002, GAP-004, GAP-005, GAP-006: UNRESOLVED_D

These gaps remain scientifically consequential under the classification rule.
They cannot be repaired in Task 100D-E0 by inventing a scientific rule or by
assuming EXP-023/EXP-024 precedent unless the frozen EXP-025 design explicitly
inherits the same definition. The current EXP-025 language is either silent or
only states compatibility without binding the disputed implementation detail.
In particular, `EXP-025-PREREGISTRATION.md` says the secondary RQ3 test is
`EXP-024-compatible`, but it does not restate the EXP-024 tie-handling or
p-value-counting sentence as an explicit inherited scientific definition.

Because no DIAGNOSTIC/EVAL outcome has been exposed, a prospective protocol
clarification may still be scientifically possible. That clarification must be
explicit and separately governed, not silently introduced during
implementation.

## Experiment Status

```text
EXP025_IMPLEMENTATION_BLOCKED_BY_PREOUTCOME_SPECIFICATION_GAP = true
EXP025_READY_FOR_FORMAL_EXECUTOR_IMPLEMENTATION = false
EXP025_NEXT_TASK = 100D_E1_PROSPECTIVE_SPECIFICATION_CLARIFICATION_REVIEW
```

## Required Flags

```text
EXP025_100D_E0_COMPLETE = true
EXP025_ORIGINAL_SPECIFICATION_GAP_COUNT = 6

EXP025_GAP_1_ID = GAP-001
EXP025_GAP_1_CLASS = D
EXP025_GAP_1_RESOLUTION = SCIENTIFICALLY_CONSEQUENTIAL_UNRESOLVED_GAP

EXP025_GAP_2_ID = GAP-002
EXP025_GAP_2_CLASS = D
EXP025_GAP_2_RESOLUTION = SCIENTIFICALLY_CONSEQUENTIAL_UNRESOLVED_GAP

EXP025_GAP_3_ID = GAP-003
EXP025_GAP_3_CLASS = C
EXP025_GAP_3_RESOLUTION = PURE_SERIALIZATION_OR_PROVENANCE_DETAIL

EXP025_GAP_4_ID = GAP-004
EXP025_GAP_4_CLASS = D
EXP025_GAP_4_RESOLUTION = SCIENTIFICALLY_CONSEQUENTIAL_UNRESOLVED_GAP

EXP025_GAP_5_ID = GAP-005
EXP025_GAP_5_CLASS = D
EXP025_GAP_5_RESOLUTION = SCIENTIFICALLY_CONSEQUENTIAL_UNRESOLVED_GAP

EXP025_GAP_6_ID = GAP-006
EXP025_GAP_6_CLASS = D
EXP025_GAP_6_RESOLUTION = SCIENTIFICALLY_CONSEQUENTIAL_UNRESOLVED_GAP

EXP025_REMAINING_SPECIFICATION_GAPS = 5
EXP025_SCIENTIFICALLY_CONSEQUENTIAL_GAPS = 5
EXP025_AMBIGUOUS_GAPS = 0

EXP025_SCIENTIFIC_DESIGN_CHANGED = false
EXP025_DIAG_DATA_ACCESSED = false
EXP025_EVAL_DATA_ACCESSED = false
EXP025_READY_FOR_FORMAL_EXECUTOR_IMPLEMENTATION = false
EXP025_NEXT_TASK = 100D_E1_PROSPECTIVE_SPECIFICATION_CLARIFICATION_REVIEW
```
