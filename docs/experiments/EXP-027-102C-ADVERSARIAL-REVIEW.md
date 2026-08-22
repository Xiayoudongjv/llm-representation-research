# EXP-027 Task 102C — Adversarial Engineering Review

Status: `EXP027_102C_ENGINEERING_AND_ADVERSARIAL_REVIEW_COMPLETE`

This review is engineering/adversarial only. It does not load the real Llama
model, does not access real EXP-027 FIT/DIAG/EVAL records, and does not compute
a scientific result or authorization.

## Repository Anchor

- Repository: `D:\Research\llm-representation-research`
- Branch: `main`
- Entry `HEAD` == `origin/main`: `f36e84a7fc883a3e5f5d777d3193e76cf6fcce13`
- Final `HEAD` == `origin/main`: `f36e84a7fc883a3e5f5d777d3193e76cf6fcce13`
- Tracked worktree: clean
- Staging: empty
- Pre-existing untracked historical evidence was left untouched.

## Result

```text
EXP026_TO_EXP027_SEMANTIC_DRIFT = NONE
EXP027_102C_ENGINEERING_AND_ADVERSARIAL_REVIEW_COMPLETE
CURRENT_NEXT_TASK = 102D_EXP027_FORMAL_PIPELINE_QUALIFICATION
```

## Semantic Trace Summary

The frozen EXP-027 rules were traced to accepted EXP-026 authority. No
`BLOCKING_SEMANTIC_DRIFT` was found.

- Compatibility estimands (`C0`, `Cself`, `D`, `Ccal`, `R`) are inherited exactly.
- Condition pooling is equal-weight arithmetic mean over the frozen ten
  conditions.
- Depth normalization uses the same `layer_index/(num_layers-1)` formula; the
  denominator adapts deterministically from Qwen `27` / OLMo `15` to Llama `15`.
- Source-coverage gate uses `ceil(L/2)`; for `L=16` this freezes as `8`.
- Spearman ties use average ranks; SDI uses population variance `ddof=0`;
  bootstrap uses `PCG64(20260819)`, `5000` replicates, 5/95 percentile endpoints.
- Profile routing is exact-match only and is a new EXP-027 operational rule,
  not a rewritten EXP-026 statistic.
- Invariance/transport/functional-binding theory terms appear only in the
  future-theory firewall, not as scientific endpoints.

## Verification Matrix

| Rule | Prereg | Frozen JSON | Baseline validator | 102C adversarial tests | Status |
| --- | --- | --- | --- | --- | --- |
| Depth normalization | YES | YES | YES | YES | PASS |
| Matrix orientation | YES | YES | PARTIAL | YES | PASS |
| Condition pooling | YES | YES | YES | YES | PASS |
| LOW-D DIAGNOSTIC/EVAL firewall | YES | YES | PARTIAL | YES | PASS |
| Technical validity boundaries | YES | YES | YES | YES | PASS |
| Exact profile routing | YES | YES | YES | YES | PASS |
| Invalidity precedes routing | YES | YES | YES | YES | PASS |
| Carrier final-norm trap | YES | YES | YES | YES | PASS |
| Last-valid-token selection | YES | YES | YES | YES | PASS |
| Class-order mapping | YES | YES | PARTIAL | YES | PASS |
| Bootstrap/statistics | YES | YES | PARTIAL | YES | PASS |
| Outcome-blind progress | YES | YES | PARTIAL | YES | PASS |
| No scientific CLI override | YES | YES | PARTIAL | YES | PASS |
| Theory contamination firewall | YES | YES | PARTIAL | YES | PASS |

`PARTIAL` in the baseline validator column means the field is checked by the
frozen config or the 102C adversarial test oracle, not by every individual
baseline assertion. The combined validation suite passes.

## Scientific Firewall

- `REAL_FIT_ACCESSED = false`
- `REAL_DIAG_ACCESSED = false`
- `REAL_EVAL_ACCESSED = false`
- `LLAMA_SCIENTIFIC_INFERENCE_PERFORMED = false`
- `SCIENTIFIC_MATRIX_COMPUTED = false`
- `SCIENTIFIC_RESULT_CREATED = false`
- `FORMAL_AUTHORIZATION_CREATED = false`
- `FORMAL_RUN_PERFORMED = false`

## Test Evidence

- `python experiments/exp027/validate_exp027_preregistration.py` → `PASS`
- `python -m pytest tests/test_exp027_preregistration.py -q` → `17 passed in 0.16s`
- `python -m pytest tests/test_exp027_102c_adversarial.py -q` → `105 passed in 5.48s`
- `python -m pytest tests/test_exp027_bootstrap_optimized_prototype.py tests/test_exp027_progress.py -q` → `13 passed, 72 warnings in 21.37s`
- `python -m py_compile tests/test_exp027_102c_adversarial.py` → `PASS`

## Artifacts

- Review document: `docs/experiments/EXP-027-102C-ADVERSARIAL-REVIEW.md`
- Machine review: `experiments/exp027/engineering/exp027_102c_adversarial_review.json`
- Adversarial tests: `tests/test_exp027_102c_adversarial.py`

## Next Step

Do not execute 102D here. The next task is:

```text
102D_EXP027_FORMAL_PIPELINE_QUALIFICATION
```
