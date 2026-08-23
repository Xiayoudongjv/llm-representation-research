# PAPER-A EXT-A Cross-Task Preregistration

Status: `FINAL_FROZEN_PRE_DATA_PROTOCOL`

Panel content status: `PANEL_CONTENT_NOT_YET_CREATED`

This document is the prospective preregistration for the single authorized
Paper-A extension. It does not create a panel, access model inference, create
results, or issue authorization.

## 1. Experiment Identity

- `EXPERIMENT_ID = PAPER-A-EXT-A`
- `TASK_ID = PA-EXT-A-001`
- `PREFERRED_ROUTE = ROUTE_A_FRESH_CROSS_TASK_REPLICATION`
- `ONE_EXTENSION_RULE = PASS`

## 2. Primary Scientific Question

When Qwen3-1.7B, OLMo-2-1B-Instruct, and Meta-Llama-3.2-1B-Instruct are held
fixed in model identity, carrier semantics, depth coordinates, fixed-readout
procedures, statistics, and routing, are the registered three-component
cross-depth compatibility profiles stable when the original EXP-024 semantic
task panel is replaced by a prospectively designed, genuinely independent
semantic/task panel?

## 3. Cross-Task Independence

- `CROSS_TASK_INDEPENDENCE_LEVEL = NEW_TASK_FAMILIES_AND_NEW_SEMANTIC_RELATIONS`
- Paraphrase-only replacement is not sufficient.
- New panel must not reuse old semantic relation families, base-content
  identities, or source-family IDs.

## 4. Model Set

Exactly three models; no fourth model:

- Qwen: `Qwen/Qwen3-1.7B`
  - revision `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`
  - 28 decoder blocks
- OLMo: `allenai/OLMo-2-0425-1B-Instruct`
  - revision `48d788eca847d4d7548f375ad03d3c9312f6139e`
  - 16 decoder blocks
- Llama: `Meta-Llama-3.2-1B-Instruct`
  - converted model hash `1ff795ff6a07e6a68085d206fb84417da2f083f68391c2843cd2b8ac6df8538f`
  - 16 logical decoder blocks
  - final hidden-state semantics `POST_FINAL_NORM_CONFIRMED`
  - `outputs.hidden_states[-1]` is forbidden as scientific carrier

## 5. Measurement Contract

Inherited from EXP-026/027:

- fixed semantic readout trained on FIT condition realizations
- `C0`, `Cself`, `Ccal`, `D = Cself - C0`, `R = Ccal - C0`
- `A_mu_sigma` FIT-only featurewise recalibration
- logistic regression contract inherited exactly
- condition pooling: equal weight over conditions
- source/target matrix orientation: rows source layers, columns target layers
- normalized depth `layer_index/(num_layers-1)`

## 6. Statistical Contract

Inherited from EXP-026/027:

- Spearman distance association
- SDI population-variance convention `numpy.var(ddof=0)`
- LOW-D mask and estimand inherited exactly
- condition-stratified source-family cluster bootstrap
- `5000` replicates, seed `20260819`, `numpy.random.PCG64`
- `numpy.percentile_method_linear`
- one-sided 95% support bounds as registered per component

## 7. Outcome Routing

See `PAPER-A-CROSS-TASK-OUTCOME-ROUTING.md`.

Primary routes: `A1` through `A6`. No route is privileged.

## 8. Panel-Authority Route

`HUMAN_AUTHORED_SOURCE_BANK_DETERMINISTIC_TRANSFORMATION`

No real source bank is created in this task.

## 9. Firewalls

- EXP-024 remains a negative result; no predictive rescue endpoint.
- EXP-028 remains paused and untouched; no paired operator-complexity
  endpoint.
- Paper-A manuscript, figures, tables, and claim prose are unchanged.

## 10. Hard Flags

- `REAL_EXT_A_PANEL_CREATED = false`
- `REAL_EXT_A_CANDIDATE_ITEMS_CREATED = false`
- `REAL_EXT_A_FIT_DATA_CREATED = false`
- `REAL_EXT_A_DIAG_DATA_CREATED = false`
- `REAL_EXT_A_EVAL_DATA_CREATED = false`
- `REAL_EXT_A_MODEL_INFERENCE_PERFORMED = false`
- `REAL_EXT_A_HIDDEN_STATES_ACCESSED = false`
- `REAL_EXT_A_RESULTS_CREATED = false`
- `REAL_EXT_A_AUTHORIZATION_CREATED = false`
- `PAPER_A_MANUSCRIPT_MODIFIED = false`
- `EXP028_MODIFIED = false`

## 11. Next Task

`PA-EXT-A-002_PANEL_CONTENT_DESIGN_AND_FREEZE`