# PAPER-A EXT-A Temporal Asset Source V5 Amendment

Status: `FINAL_FROZEN_PRE_DATA_TEMPORAL_ASSET_SOURCE_POLICY`

This is a prospective pre-data amendment. It resolves only the temporal
semantic-asset source/provenance procedure gap that blocked
`PA-EXT-A-005`. It does not change the scientific question, task families,
semantic relations, dataset shape, generator semantics, measurement contract,
statistics, outcome routing, model set, carrier rules, or one-extension
stopping rule.

## 1. Why V5

V4 froze:

`TEMPORAL_SOURCE_POLICY = INTERNAL_STRUCTURED_ASSET_BANK`

During `PA-EXT-A-005`, that policy was found operationally incomplete: the V3
temporal family requires natural-language `EVENT` assets and a frozen
composition/render path, but no executable source procedure existed for
creating those internal temporal event assets.

No real EXT-A asset bank existed. No tested-model inference occurred. This
amendment is therefore `PRE-INFERENCE` and `OUTCOME_UNEXPOSED`.

## 2. Authority Preservation

Historical V4 authority remains preserved.

- Protocol SHA-256:
  `78e58c43c7fabfafaa03084ef17f9c5ff4c02665d242aa57b9f70a9d3b793e5d`
- V3 content-design SHA-256:
  `205376bbd8704862de2cafeb1fd09719b498688532e6c54aec3a2326b71f0462`
- V3 pipeline generator SHA-256:
  `6508490ec2141f0531f7e61a24c3496e00705fd85d34bc5ca725d24bd38b3953`
- V3 pipeline validator SHA-256:
  `c344ff526948b9b0e98f305095164a643478080427f84786d02668776fb22cb1`
- V4 source manifest SHA-256:
  `72bf8de42c315e390269eeb874ee89828c7cc1541e2d4171fd5dc8ae2215faf9`
- V4 binding SHA-256:
  `b23fc6329b7863bfa0a7f80c06bf582706ce1457c5b04ecffaefd74bfefddc7f`

## 3. Route Selection

Evaluated routes:

| Route | Decision |
| --- | --- |
| TORQUE external temporal source | `DO_NOT_SELECT`: license, deterministic extraction, V3 schema, and final-text reuse gates all fail |
| MATRES external temporal source | `DO_NOT_SELECT`: dataset-level license gate fails despite structural event-pair annotations |
| Programmatic internal temporal assets | `INELIGIBLE`: placeholder-only event tokens would materially change the frozen natural-language construct |
| Executable internal structured asset bank | `SELECTED` |

Selected route:

`ADOPT_EXECUTABLE_INTERNAL_TEMPORAL_SOURCE`

New temporal source policy:

`EXECUTABLE_INTERNAL_STRUCTURED_ASSET_BANK`

External selected source:

`NONE`

## 4. Frozen Internal Procedure

1. The future asset-authoring task creates a fixed human-authored structured
   event-pair lexicon, with no LLM generation and no model-outcome access.
2. The lexicon is authoritatively sized at 220 event-pair source assets, one
   per frozen V3 temporal source family:
   10 conditions x (6 FIT + 8 DIAG + 8 EVAL).
3. Each source asset provides two natural-language `EVENT` atoms and exactly
   one temporal orientation: before, after, or simultaneous. Causal and
   counterfactual content is forbidden.
4. A deterministic cell mapping assigns event-pair source assets to V3 cells
   in canonical lexicographic order. The existing V3 pipeline remains the
   final composition/render authority and creates 440 final records.
5. No post-hoc selection, surplus authoring, tested-model filtering, or
   expected-profile-based filtering is permitted.

`REAL_EXT_A_TEMPORAL_ASSETS_CREATED = false`

`REAL_EXT_A_SEMANTIC_ASSET_BANK_CREATED = false`

`REAL_EXT_A_PANEL_CREATED = false`

## 5. What Does Not Change

- `SCIENTIFIC_QUESTION_MODIFIED = false`
- `TASK_FAMILY_SET_MODIFIED = false`
- `SEMANTIC_RELATION_SET_MODIFIED = false`
- `DATASET_SHAPE_MODIFIED = false`
- `GENERATOR_MODIFIED = false`
- `MEASUREMENT_CONTRACT_MODIFIED = false`
- `STATISTICAL_CONTRACT_MODIFIED = false`
- `OUTCOME_ROUTING_MODIFIED = false`
- `MODEL_CONTRACT_MODIFIED = false`
- `CARRIER_CONTRACT_MODIFIED = false`

## 6. Source Manifest

Path:
`experiments/paper_a_ext_a/paper_a_ext_a_temporal_asset_source_manifest.json`

This manifest contains the frozen source policy, route evaluation, canonical
relation mapping, deterministic creation rule, provenance requirements,
freshness policy, V3 compatibility, V4 relationship, and hard flags.

## 7. Raw-Text Firewall

- `FINAL_BENCHMARK_TEXT_REUSED = false`
- `EXTERNAL_RAW_TEXT_USED_AS_FINAL_PANEL_TEXT = false`
- `LLM_GENERATED_TEMPORAL_CONTENT = false`

Final panel text remains the deterministic V3 rendered output. Event surface
atoms are allowed only as renderer inputs, not as copied final benchmark text.

## 8. Hard Flags

- `REAL_EXT_A_TEMPORAL_ASSETS_CREATED = false`
- `REAL_EXT_A_SEMANTIC_ASSET_BANK_CREATED = false`
- `REAL_EXT_A_SOURCE_BANK_CREATED = false`
- `REAL_EXT_A_PANEL_CREATED = false`
- `REAL_EXT_A_MODEL_INFERENCE_PERFORMED = false`
- `REAL_EXT_A_RESULTS_CREATED = false`
- `REAL_EXT_A_AUTHORIZATION_CREATED = false`
- `V3_PIPELINE_MODIFIED = false`
- `V4_AUTHORITY_PRESERVED = true`
- `PAPER_A_MANUSCRIPT_MODIFIED = false`
- `EXP028_MODIFIED = false`

## 9. Next Task

`PA-EXT-A-005_REAL_SEMANTIC_ASSET_CURATION_AND_PANEL_FREEZE_RETRY`
