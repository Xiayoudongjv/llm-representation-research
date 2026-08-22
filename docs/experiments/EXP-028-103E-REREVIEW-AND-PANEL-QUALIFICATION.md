# EXP-028 Task 103E Rereview and Fresh-Panel Qualification

**Status:** `EXP028_103E_STATUS = COMPLETE`
**Task:** `103E_EXP028_RUNNER_REREVIEW_AND_FRESH_PANEL_GENERATION_QUALIFICATION`
**Entry HEAD:** `d636b51618cbaaca5c27713487c145bcf7e76ccd`
**Final HEAD:** `d636b51618cbaaca5c27713487c145bcf7e76ccd`
**origin/main:** `d636b51618cbaaca5c27713487c145bcf7e76ccd`

This is an engineering-only, pre-scientific-data qualification. It does not create
a final EXP-028 scientific panel, does not create a formal authorization, and
does not run EXP-028 scientifically.

## Rereview Results

- `RUNNER_REREVIEW = PASS`
- `CONTRACT_TO_CODE_TRACEABILITY = PASS`
- `OUTCOME_BLINDNESS_REREVIEW = PASS`
- `AUTHORIZATION_REREVIEW = PASS`
- `PUBLICATION_REREVIEW = PASS`

The formal-run path now rejects missing, synthetic, unfrozen, wrong-SHA, and
freshness-violating panels before scientific execution. Authorization validation
now also rejects a bound-HEAD mismatch.

## Panel Machinery

- Panel contract: `PASS`
- Panel generator: `PASS`
- Panel validator: `PASS`
- Historical exclusion index: `PASS`
- Freshness validation: `PASS`
- Split integrity validation: `PASS`
- Panel freeze identity: `PASS`
- Formal-run rejects synthetic panel: `PASS`

The generator is deterministic and does not load model weights. It does not
introduce a random seed. The final scientific panel is not generated here; only
a labeled synthetic non-scientific fixture is produced for rejection testing.

## Implemented Files

- `experiments/exp028/exp028_panel_lib.py`
- `experiments/exp028/build_exp028_exclusion_index.py`
- `experiments/exp028/generate_exp028_panel.py`
- `experiments/exp028/validate_exp028_panel.py`
- `experiments/exp028/engineering/exp028_historical_exclusion_index.json`
- `experiments/exp028/engineering/exp028_synthetic_panel_fixture.json`
- `experiments/exp028/engineering/exp028_103e_rereview_and_panel_qualification.json`
- `tests/test_exp028_panel.py`

Modified:
- `experiments/exp028/run_exp028.py`
- `experiments/exp028/engineering/exp028_runner_synthetic_qualification.json`

## Key Hashes

- Runner SHA-256: `2c377f019bc17eb534febe46b6221805510dabdbce9b5133d5a8a297ede6bd08`
- Result validator SHA-256: `61c8b2c987f6c1261e7b14a1a38b871277baa3343745cd42919c0655e0c30093`
- Panel generator SHA-256: `0b944c366e1e41dc0df513166d9cde716e44f0682b04fbbb494eafa3362f22ef`
- Panel validator SHA-256: `7cc84a3504df9e4d278ac4ed22228e992fb0cb3fc4ba292e511324c1eb49d864`
- Historical exclusion index SHA-256: `b261cf1f15d916fa96cb5fa0cbdd74a4289155892142ad9f2939542271588658`
- Synthetic fixture SHA-256: `7b20564c895afe49a8ae1a8b8ee142a570a26ba5f09d0c05b63662b7ec9cd6bf`
- Qualification artifact SHA-256: `e4c84ffc4a1c3ae4ac760371ac266bb4cdcc4194fff49a6b0083453fd07c7043`

## Validation Gates

- Preregistration validator: `PASS`
- Original 103D tests: `49/49`
- Total EXP-028 focused tests: `74/74`
- Synthetic panel qualification: `PASS`
- `py_compile`: `PASS`
- `git diff --check`: clean

Two known `sklearn` deprecation warnings remain. They are classified as
`KNOWN_DEPRECATION` because the frozen logistic-regression penalty surface must
not be changed.

## Firewall

- `REAL_EXP028_FIT_ACCESSED = false`
- `REAL_EXP028_DIAG_ACCESSED = false`
- `REAL_EXP028_EVAL_ACCESSED = false`
- `REAL_EXP028_MODEL_INFERENCE_PERFORMED = false`
- `FINAL_EXP028_SCIENTIFIC_PANEL_CREATED = false`
- `EXP028_AUTHORIZATION_CREATED = false`
- `EXP028_FORMAL_RUN_PERFORMED = false`
- `EXP028_CANONICAL_RESULT_CREATED = false`
- `PREREGISTRATION_MODIFIED = false`
- `SCIENTIFIC_CONFIG_MODIFIED = false`

## Next Task

`103F_EXP028_FRESH_SCIENTIFIC_PANEL_GENERATION_VALIDATION_AND_FREEZE`
