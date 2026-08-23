# Paper-A EXT-A External Semantic Asset Source Review

Status: `PA_EXT_A_003A_EXTERNAL_SEMANTIC_ASSET_SOURCE_FREEZE`

This is a source-selection/provenance review. It does not create a real
semantic asset bank, source bank, panel, model inference, result, or
authorization. Final panel text remains the output of the qualified V3
deterministic renderer.

## 1. Source Principle

`BORROW_SEMANTIC_STRUCTURE_NOT_FINAL_BENCHMARK_ITEMS`

External resources may contribute canonicalized structured objects such as
`(subject, relation, object)`, `(event_a, temporal_relation, event_b)`, or
`(part, whole)`. They must not contribute final experiment text, public
benchmark questions, stories, answers, or distractors.

## 2. Task-Family Source Decisions

| Task family | Source policy | Selected source |
| --- | --- | --- |
| `exta_tf_spatial` | `EXTERNAL_STRUCTURED_ASSET_SOURCE` | StepGame HF dataset artifact, MIT metadata |
| `exta_tf_temporal` | `INTERNAL_STRUCTURED_ASSET_BANK` | none external |
| `exta_tf_quantitative` | `PROGRAMMATIC_GENERATION` | none external |
| `exta_tf_mereological` | `EXTERNAL_STRUCTURED_ASSET_SOURCE` | WordNet 3.0, Princeton WordNet License |

`MULTI_SOURCE_EXTERNAL_COMBINATION_ACTIVE = false`

No family combines multiple external datasets. The selected source set is
frozen now and cannot be expanded post hoc if asset yield is low.

## 3. Candidate Review

| Candidate | License | License verified | Use |
| --- | --- | --- | --- |
| StepGame | MIT (HF dataset metadata) | `PASS` | `STRUCTURED_ASSET_SOURCE` |
| WordNet 3.0 | Princeton WordNet License / SPDX WordNet | `PASS` | `STRUCTURED_ASSET_SOURCE` |
| TORQUE | unresolved dataset license | `AMBIGUOUS` | `DO_NOT_USE` |
| MATRES | unresolved / likely LDC-derived | `AMBIGUOUS` | `DO_NOT_USE` |
| TimeBank | LDC restricted | `FAIL` | `DO_NOT_USE` |
| MAVEN-ERE | GPLv3 repo + mixed underlying CC BY-SA | `AMBIGUOUS` | `DO_NOT_USE` |

License calls are dataset/resource-specific. Code-repository licenses and
paper/arXiv licenses are not used as dataset licenses unless they explicitly
cover the selected data artifact.

## 4. Temporal Decision Rationale

No examined public temporal-relation dataset had a sufficiently clear
dataset-level license for external structured extraction. Temporal assets
therefore remain under the existing V3 internal structured asset-bank
contract, with no external source selected.

## 5. V3 Compatibility

V3 currently has `transformation_contract.source_owner =
HUMAN_AUTHORED_SOURCE_BANK` and no explicit external-asset provenance policy.
External structured provenance therefore requires a narrow prospective V4
provenance amendment.

`V4_AMENDMENT_REQUIRED = true`

V4 changes only source/provenance policy. It does not change the scientific
question, task families, semantic relations, dataset shape, generator
semantics, measurement, statistics, routing, models, carriers, or frozen
conditions.

## 6. Contamination Interpretation

External sources are treated as possible pretraining exposure/prior art only.
The extension does not claim novel-fact generalization or
unseen-world-knowledge reasoning. Its scientific purpose is cross-task
measurement compatibility.

`FINAL_BENCHMARK_TEXT_REUSED = false`

`EXTERNAL_RAW_TEXT_USED_AS_FINAL_PANEL_TEXT = false`

## 7. Hard Flags

- `REAL_EXT_A_SEMANTIC_ASSET_BANK_CREATED = false`
- `REAL_EXT_A_SOURCE_BANK_CREATED = false`
- `REAL_EXT_A_PANEL_CREATED = false`
- `REAL_EXT_A_MODEL_INFERENCE_PERFORMED = false`
- `REAL_EXT_A_RESULTS_CREATED = false`
- `V3_PIPELINE_MODIFIED = false`
- `PAPER_A_MANUSCRIPT_MODIFIED = false`
- `EXP028_MODIFIED = false`

## 8. Next Task

`PA-EXT-A-004_MINIMAL_PRE_DATA_RELEASE_GATE`