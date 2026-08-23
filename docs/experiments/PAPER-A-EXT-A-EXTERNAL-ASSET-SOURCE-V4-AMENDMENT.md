# PAPER-A EXT-A External Asset Source V4 Amendment

Status: `FINAL_FROZEN_PRE_DATA_EXTERNAL_ASSET_SOURCE_POLICY`

This is a prospective pre-data provenance amendment. It permits structured
semantic assets to be derived from explicitly frozen external sources under
the existing deterministic V3 composition/render path. It does not change the
scientific question, task families, semantic relations, dataset shape,
generator semantics, measurement contract, statistics, outcome routing, model
set, carrier rules, or one-extension stopping rule.

## 1. Why V4

V3 fixed `source_owner = HUMAN_AUTHORED_SOURCE_BANK` but did not explicitly
authorize external structured-asset provenance. To reduce manual authoring
while preserving cross-task independence, a narrow source/provenance policy is
required.

`V4_AMENDMENT_REQUIRED = true`

## 2. Authority Preservation

- Protocol SHA-256:
  `78e58c43c7fabfafaa03084ef17f9c5ff4c02665d242aa57b9f70a9d3b793e5d`
- V3 content-design SHA-256:
  `205376bbd8704862de2cafeb1fd09719b498688532e6c54aec3a2326b71f0462`
- V3 pipeline generator SHA-256:
  `6508490ec2141f0531f7e61a24c3496e00705fd85d34bc5ca725d24bd38b3953`
- V3 pipeline validator SHA-256:
  `c344ff526948b9b0e98f305095164a643478080427f84786d02668776fb22cb1`

These authority bytes remain unchanged. V4 adds a separate source manifest
and binding; it does not rewrite V3.

## 3. What Changes

- `SEMANTIC_ASSET_SOURCE_POLICY`
- `EXTERNAL_SOURCE_PROVENANCE`
- `EXTERNAL_SOURCE_LICENSE_POLICY`
- `CONTAMINATION_INTERPRETATION`

## 4. What Does Not Change

- `SCIENTIFIC_QUESTION_MODIFIED = false`
- `TASK_FAMILY_SET_MODIFIED = false`
- `SEMANTIC_RELATION_SET_MODIFIED = false`
- `DATASET_SHAPE_MODIFIED = false`
- `GENERATOR_SEMANTICS_MODIFIED = false`
- `MEASUREMENT_CONTRACT_MODIFIED = false`
- `STATISTICAL_CONTRACT_MODIFIED = false`
- `OUTCOME_ROUTING_MODIFIED = false`
- `MODEL_CONTRACT_MODIFIED = false`
- `CARRIER_CONTRACT_MODIFIED = false`

## 5. Frozen Source Decisions

| Task family | Source policy | Selected source |
| --- | --- | --- |
| `exta_tf_spatial` | `EXTERNAL_STRUCTURED_ASSET_SOURCE` | StepGame HF dataset artifact, MIT metadata |
| `exta_tf_temporal` | `INTERNAL_STRUCTURED_ASSET_BANK` | none external |
| `exta_tf_quantitative` | `PROGRAMMATIC_GENERATION` | none external |
| `exta_tf_mereological` | `EXTERNAL_STRUCTURED_ASSET_SOURCE` | WordNet 3.0, Princeton WordNet License |

External sources contribute canonicalized relation structure only. Final
panel text remains V3-rendered deterministic output.

## 6. License Firewall

Selected external resources have dataset/resource-specific licenses:
- StepGame: MIT, recorded in the Hugging Face dataset artifact metadata.
- WordNet 3.0: Princeton WordNet License, SPDX identifier `WordNet`.

Code-repository and paper licenses are not treated as dataset licenses unless
they explicitly cover the selected data artifact.

## 7. Contamination Firewall

`FINAL_BENCHMARK_TEXT_REUSED = false`

`EXTERNAL_RAW_TEXT_USED_AS_FINAL_PANEL_TEXT = false`

The experiment may not claim novel-fact generalization or
unseen-world-knowledge reasoning. External sources are treated as possible
pretraining exposure/prior art only.

## 8. Source Manifest

Path:
`experiments/paper_a_ext_a/paper_a_ext_a_external_asset_source_manifest.json`

V4 binding path:
`experiments/paper_a_ext_a/paper_a_ext_a_external_asset_source_v4_binding.json`

## 9. Hard Flags

- `REAL_EXT_A_SEMANTIC_ASSET_BANK_CREATED = false`
- `REAL_EXT_A_SOURCE_BANK_CREATED = false`
- `REAL_EXT_A_PANEL_CREATED = false`
- `REAL_EXT_A_MODEL_INFERENCE_PERFORMED = false`
- `REAL_EXT_A_RESULTS_CREATED = false`
- `V3_PIPELINE_MODIFIED = false`
- `PAPER_A_MANUSCRIPT_MODIFIED = false`
- `EXP028_MODIFIED = false`

## 10. Next Task

`PA-EXT-A-004_MINIMAL_PRE_DATA_RELEASE_GATE`