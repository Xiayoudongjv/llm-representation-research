# Paper-A Cross-Task Task-Family Review

Status: `PA_EXT_A_002_TASK_FAMILY_REVIEW`

This is a prospective design review of the abstract new task universe. It does
not create real items and does not use model outcomes.

## 1. Independence Target

Required:

- `NEW_TASK_FAMILIES = true`
- `NEW_SEMANTIC_RELATIONS = true`

Weak independence forms are rejected: new items, new lexical realizations, new
templates only, or paraphrase replication.

## 2. Old Universe

Old EXP-024 semantic classes:

- `logic`
- `causality`
- `analogy`
- `definition`

The old panel is a four-way semantic-relation classification over those
classes, with ten surface conditions.

## 3. Proposed New Universe

Four new task families:

1. `exta_tf_spatial`
2. `exta_tf_temporal`
3. `exta_tf_quantitative`
4. `exta_tf_mereological`

Four new semantic relations, one per task family:

1. `exta_rel_spatial_configuration`
2. `exta_rel_temporal_order`
3. `exta_rel_quantitative_comparison`
4. `exta_rel_part_whole`

## 4. Distinctness Assessment

| New family | Old class it most resembles | Why it is distinct |
| --- | --- | --- |
| `exta_tf_spatial` | none | static location/containment; no entailment, cause, analogy, or definition |
| `exta_tf_temporal` | `causality` | order/overlap only; no causal or counterfactual marker allowed |
| `exta_tf_quantitative` | `logic` | magnitude relation; no truth/entailment operator |
| `exta_tf_mereological` | `definition` | part-whole world relation; no dictionary-style equivalence |

The temporal-vs-causality and part-whole-vs-definition boundaries are the
closest. They are controlled by explicit forbidden-relation and invalidity
rules in the content design, not by author discretion.

## 5. Comparability

The new universe preserves:

- four-way fixed-readout classification
- two explicit arguments
- source-family and partition structure
- ten deterministic surface conditions
- `FIT=6`, `DIAG=8`, `EVAL=8` per class per condition

It does not redefine distance, SDI, LOW-D, bootstrap, routing, carriers, or
models.

## 6. Outcome Neutrality

No task family was selected because it is expected to reproduce Qwen target
dominance, OLMo source dominance, Llama target dominance, or any LOW-D state.
The design is claim-neutral.

## 7. Residual Limitations

- Relation-specific vocabulary cannot be completely eliminated without
  unnatural text; the design uses multiple lexical realizations and static
  audits.
- Some entity-type differences across task families are inherent; the
  design balances entity categories and documents any residual structure.
- Inherent task difficulty may differ; this is controlled outcome-neutrally,
  not by model outcomes.

## 8. Verdict

- `TASK_FAMILY_SET_FROZEN = PASS`
- `SEMANTIC_RELATION_SET_FROZEN = PASS`
- `OLD_PANEL_SEMANTIC_EXCLUSION = PASS`
- `OUTCOME_NEUTRAL_DESIGN = PASS`

## 9. Hard Flags

- `REAL_EXT_A_SOURCE_BANK_CREATED = false`
- `REAL_EXT_A_PANEL_CREATED = false`
- `REAL_EXT_A_CANDIDATE_ITEMS_CREATED = false`
- `REAL_EXT_A_MODEL_INFERENCE_PERFORMED = false`