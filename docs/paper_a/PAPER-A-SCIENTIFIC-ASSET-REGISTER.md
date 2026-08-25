# Paper A Scientific Asset Register

Status: `READY_FOR_PAPER_A_SCIENCE_FREEZE`

This register is a manuscript-facing inventory. It points to canonical result
artifacts and does not contain newly computed science. Hashes are verified by
`experiments/paper_a/canonical/validate_paper_a_canonical_register.py`.

## Complete inventory by scientific role

| Asset ID | Experiment / path | SHA-256 | Canonical status | Result class | Scientific role / model / scope | Confirmation | Manuscript use and claim boundary |
|---|---|---|---|---|---|---|---|
| A17 | EXP-017; `docs/experiments/EXP-017.md` | `3c25d2515dd60b941196608e9c2b2be43aa25c4924028271f74db310f3cadc5a` | registered historical boundary | `CORE_REGISTERED_NEGATIVE` | Qwen behavioral steering; preregistered transitions | confirmatory | behavioral effect failed; no representation-behavior link |
| A18 | EXP-018; `docs/experiments/EXP-018.md` | `93c003edc1c44b0273266f9dda9bc41ac0eaaa9e3572a64e62804fcdbf1e7e2e` | registered historical boundary | `CORE_HETEROGENEITY` | Qwen/Gemma held-out transition and relational validation | confirmatory | transition evidence retained; relational validation failed |
| A19 | EXP-019; `docs/experiments/EXP-019.md` | `4c616d05610bef24da4dc94989eb13281798d8bb2504ddd377dd522eb70b06f7` | registered historical boundary | `OUT_OF_SCOPE_FOR_PAPER_A` | independent behavioral evaluator/generalization | confirmatory | evaluator boundary; not representation evidence |
| A20 | EXP-020A; `experiments/exp020/results/exp020a_results.json` | `c603b763c5b5723b002d67ce71a073beba9668bf8bc49e0a215cc54d5f82e26a` | engineering result | `ENGINEERING_ONLY` | Qwen3-4B execution/lifecycle qualification | engineering | never use as fixed-readout compatibility evidence |
| A21 | EXP-021; `docs/experiments/EXP-021-STAGE-Q-IMPLEMENTATION-REVIEW-CLOSURE.md` | `eb9fc53e9f31f3b1bfcb92249a9400771d115e7b8f98589067ffe960531ef7c5` | implementation review | `ENGINEERING_ONLY` | Stage-Q / hook-oracle runtime infrastructure | engineering | no Paper A scientific claim |
| A22 | EXP-022A; `experiments/exp022a/results/exp022a_results.json` | `2a26f77116acf37aac6462b997300d890445cac0f0ec98ffc5ec710b36a975c9` | canonical result | `CORE_HETEROGENEITY` | Qwen split-direction paraphrase/original transfer | confirmatory | split-dependent operational evidence |
| A23 | EXP-023; `experiments/exp023/results/exp023_results.json` | `f30591ad942e82a322e594695ce1d5023586261fd7b8bccaa208b0d46f388000` | canonical result | `CORE_REGISTERED_NEGATIVE` | Qwen split-generalization calibration | confirmatory | cross-split `NO_REPLICATION` |
| A24 | EXP-024; `experiments/exp024/results/exp024_results.json` | `50a6ea72dbb9c33ae8ec15d0e2ad31b32ebe0cf299679875fe7b34fb6cabcb69` | canonical result | `CORE_REGISTERED_NEGATIVE` | Qwen ten-condition compatibility predictor | confirmatory | preregistered predictor unsupported |
| A25 | EXP-025; `experiments/exp025/results/exp025_results.json` | `bbac2f03b24bdf2ec93485c201d3c0cf50588ed51659e607bb97b231181765a9` | canonical result | `CORE_HETEROGENEITY` | OLMo ten-condition predictor and D/G inference | confirmatory | predictor unsupported; D/G split/condition heterogeneity |
| A26 | EXP-026; `experiments/exp026/results/exp026_results.json` | `9a5bed41b432e2f89b0873869d76e1f5775f9b38caff9472553fca335bbba551` | canonical result | `CORE_CONFIRMATORY` | Qwen3-1.7B and OLMo-2-1B directed matrices | confirmatory | primary three-model profile evidence |
| A27 | EXP-027; `experiments/exp027/results/exp027_results.json` | `1f15027d17456f5dc8ff4803452c732af8ba464f70e537195b8833d9d44f6c6d` | canonical result | `CORE_CONFIRMATORY` | Meta-Llama-3.2-1B-Instruct directed matrix | confirmatory | registered third-model profile |
| ADIR | Directionality closure; `experiments/paper_a/directionality_exploratory_closure.json` | `8ea5dbe996c3d3c061e54bbf2d31242426d8e9b2b7fb814266891d203d33bccc` | closed exploratory closure | `EXPLORATORY_SECONDARY` | three-model post-hoc asymmetry summaries | exploratory | C8 only; no causal/geometric overclaim |
| AEXT | EXT-A; `docs/paper/extension/PA-EXT-A-005R2-PAUSE-STATE.md` | `4b4b7882fe1add37539b09b11ddec1dba962defaee64cc5443543c8a955fb41e` | paused pre-inference lineage | `OPTIONAL_PAUSED` | external semantic panel attempt | not run | C9 not established; no model result |
| BEXT | EXT-B; `docs/experiments/PAPER-A-EXT-B-TERMINAL-DATASET-FAILURE.md` | `28a97957d7fcf23c8f3241a8e6cf7f0433e68a2bf5b0b67923681bb16ea32f0e` | terminated at data gate | `TERMINATED_DATASET_GATE` | external panel construction | not run | C9 not established; no model result |

The table is organized by evidentiary role rather than experiment chronology.
`CANONICAL_STATUS` describes the repository authority used here; it does not
upgrade an engineering or terminated asset into scientific evidence.

## Primary operational compatibility evidence

| Asset | Canonical artifact | SHA-256 | Role and scope |
|---|---|---|---|
| EXP-026 | `experiments/exp026/results/exp026_results.json` | `9a5bed41b432e2f89b0873869d76e1f5775f9b38caff9472553fca335bbba551` | Confirmatory multi-model operational compatibility matrices; Qwen and OLMo profiles |
| EXP-027 | `experiments/exp027/results/exp027_results.json` | `1f15027d17456f5dc8ff4803452c732af8ba464f70e537195b8833d9d44f6c6d` | Confirmatory registered third-model profile; Meta-Llama-3.2-1B-Instruct |

These assets support the scoped depth-variation and three-model profile claims;
they do not establish architecture-causal explanations or universal laws.

## Restricted recoverability evidence

EXP-026 and EXP-027 provide the registered restricted LOW-D recovery profile.
Recovery is supported for OLMo and Llama but not Qwen. This is a conditional,
model-profile result, not a uniform guarantee.

## Model-profile evidence

| Model | Distance support | SDI class | Restricted recovery |
|---|---|---|---|
| Qwen3-1.7B | `POSITIVE_SUPPORTED` | `TARGET_DOMINANT` | `NOT_SUPPORTED` |
| OLMo-2-1B | `POSITIVE_SUPPORTED` | `SOURCE_DOMINANT` | `SUPPORTED` |
| Meta-Llama-3.2-1B-Instruct | `POSITIVE_SUPPORTED` | `TARGET_DOMINANT` | `SUPPORTED` |

The corresponding verified values are in the machine-readable SSOT, including
field-level provenance for every number.

## Registered negative evidence

| Asset | Canonical artifact | SHA-256 | Boundary |
|---|---|---|---|
| EXP-024 | `experiments/exp024/results/exp024_results.json` | `50a6ea72dbb9c33ae8ec15d0e2ad31b32ebe0cf299679875fe7b34fb6cabcb69` | Preregistered compatibility predictor unsupported |
| EXP-025 | `experiments/exp025/results/exp025_results.json` | `bbac2f03b24bdf2ec93485c201d3c0cf50588ed51659e607bb97b231181765a9` | Predictor unsupported; D/G outcomes heterogeneous |
| EXP-023 | `experiments/exp023/results/exp023_results.json` | `f30591ad942e82a322e594695ce1d5023586261fd7b8bccaa208b0d46f388000` | Cross-split `NO_REPLICATION` for G_cal |
| EXP-022A | `experiments/exp022a/results/exp022a_results.json` | `2a26f77116acf37aac6462b997300d890445cac0f0ec98ffc5ec710b36a975c9` | Split-dependent evidence; no uniform mechanism support |

## Heterogeneity evidence

EXP-022A, EXP-023, and EXP-025 are registered as heterogeneity/boundary
evidence. Split and condition dependence is part of the result, not a reason
to select favorable subsets.

## Directionality exploratory evidence

`experiments/paper_a/directionality_exploratory_closure.json` is an
`EXPLORATORY_SECONDARY` asset (SHA-256
`8ea5dbe996c3d3c061e54bbf2d31242426d8e9b2b7fb814266891d203d33bccc`). Its
status is `CLOSED_NO_FURTHER_MATRIX_MINING`; it supports only the scoped
exploratory C8 wording.

## Research-lineage and engineering/background assets

- EXP-017: `docs/experiments/EXP-017.md`, behavioral effect failed and the
  representation-behavior link was not supported; registered negative boundary.
- EXP-018: `docs/experiments/EXP-018.md`, transition validation passed but
  relational validation failed and split generalization was mixed; registered
  transition evidence with a relational ceiling.
- EXP-019: `docs/experiments/EXP-019.md`, independent behavioral generalization
  failed; evaluator/dataset boundary, not Paper A representation evidence.
- EXP-020A: `experiments/exp020/results/exp020a_results.json` is engineering
  and execution qualification context. It is **not** fixed-readout
  compatibility evidence.
- EXP-021: `docs/experiments/EXP-021-STAGE-Q-IMPLEMENTATION-REVIEW-CLOSURE.md`
  remains `ENGINEERING_ONLY`; its runtime qualification is not a Paper A
  scientific result.

## Terminated external-panel extensions

- EXT-A: `docs/paper/extension/PA-EXT-A-005R2-PAUSE-STATE.md` (SHA-256
  `4b4b7882fe1add37539b09b11ddec1dba962defaee64cc5443543c8a955fb41e`) is
  `OPTIONAL_PAUSED`; no canonical panel or model inference was created.
- EXT-B: `docs/experiments/PAPER-A-EXT-B-TERMINAL-DATASET-FAILURE.md` (SHA-256
  `28a97957d7fcf23c8f3241a8e6cf7f0433e68a2bf5b0b67923681bb16ea32f0e`) is
  `TERMINATED_DATASET_GATE`; no model inference or scientific result exists.

## Explicit claim boundaries

Paper A does not claim cross-task robustness (C9), latent geometry, causal
mechanism, or semantic equivalence (C10). CKA is `NO_GO_REQUIRES_MODEL_RERUN_LOW_INCREMENTAL_VALUE`;
SVCCA is `DO_NOT_ADD`. Directionality is closed after the registered
exploratory closure. EXP-021 remains engineering-only.

## Future candidate experiments

A fourth model is a `FUTURE_CANDIDATE_LAB_RESOURCE_DEPENDENT` only. It is not
an active Paper A experiment and does not block the science freeze.
