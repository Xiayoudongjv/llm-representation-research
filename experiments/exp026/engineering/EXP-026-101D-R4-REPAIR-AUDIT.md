# EXP-026 Task 101D-R4 Repair Audit

Status: `READY_FOR_FINAL_R4_VERIFICATION`

## Scope

Task 101D-R4 repaired only normalized pair-distance construction and its
qualification surface. The frozen quantity remains
`|d(i)-d(j)| = |i-j|/(L-1)` with `d(l)=l/(L-1)`. Production now computes the
integer layer gap first and performs one division by the shared denominator.
No rounding, epsilon, tolerance grouping, bucketization, or raw-index result
semantics were introduced.

Code commits:

- `daca7d0fe9f991e758dff895274c2803b99478c4` — normalized-distance repair and targeted tests.
- `9b454c0ebb2ac2a5a829f268777241615c3b2f9a` — R4 qualification readiness-label alignment.

Current runner SHA-256:

`6ab29c35889ce35b9d4bc9ee98d2665865a088312940f10815714a574d2060a0`

## Targeted numerical qualification

All required checks passed:

- `NORMALIZED_DISTANCE_L4_TIE_TEST`
- `NORMALIZED_DISTANCE_L16_TIE_TEST`
- `NORMALIZED_DISTANCE_L28_TIE_TEST`
- `NORMALIZED_DISTANCE_SYMMETRY_TEST`
- `NORMALIZED_DISTANCE_BOUNDARY_TEST`
- `DISTANCE_RANK_CLASS_GOLDEN`
- `DISTANCE_RHO_TIE_GOLDEN`
- `OLD_FLOAT_SUBTRACTION_SABOTAGE`
- `RAW_INDEX_DISTANCE_SEMANTIC_SABOTAGE`

Qwen's 28 layers produce exactly 27 off-diagonal distance classes. OLMo's 16
layers produce exactly 15. Every pair sharing an integer gap has one exact
distance value. The exposing fixture now gives the independently specified rho
`-0.30641293851417056`; the old coordinate-subtraction implementation fails the
tie-rank golden.

## Regression and qualification evidence

- `python -m compileall src experiments`: PASS
- `tests/test_exp026_runner.py`: 94 passed
- static preflight: PASS
- R3-1, R3-2, R3-3, and R3-5 regressions: PASS
- B1, B2, B3, B4, and M3 regressions: PASS
- publication-race and technical-validity regressions: PASS
- offline neutral engineering qualification: PASS
- shared-executor synthetic formal qualification: PASS

Versioned engineering qualification:

- path: `exp026_runner_qualification_101d_r4.json`
- SHA-256: `bbce631a27e20762212eb905278b4398c4850485faacd62e865b2f7a286f2e2d`

Versioned formal-pipeline qualification:

- path: `exp026_formal_pipeline_qualification_101d_r4.json`
- SHA-256: `f474e28d04362fdebcf6eee5348a8b558a898124bc3c01cb7e053add59051690`
- supersedes: `ea44190d0824bdacca73de58af44a700712a8a30d1f6aab6ea3b8ef92ac62da8`
- reason: `NORMALIZED_DISTANCE_FLOAT_TIE_SPLITTING_REPAIRED_BEFORE_SCIENTIFIC_EXPOSURE`

## Science firewall

- real FIT accessed: false
- real DIAGNOSTIC accessed: false
- real EVAL accessed: false
- real scientific inference performed: false
- valid scientific result count: 0
- formal authorization created: false

The R4 self-qualification does not authorize formal execution. Its only
readiness state is `READY_FOR_FINAL_R4_VERIFICATION`.
