# Paper-A EXT-B Final Pre-Generation Amendment V2

Status: `FINAL_PRE_GENERATION_PRE_MODEL_OUTCOME`

This is the final scientific construction amendment for EXT-B. It was frozen
before production data composition, model authorization, model inference, or
scientific outcome observation. No Amendment V3 for scientific construction is
permitted.

## Provenance and parent authorities

- Original EXT-B freeze: `640ef4cca8c012491c81eed32215b2abfbe7f07e`
- Amendment V1: `9e9cae6d542816e8cf5668955f948f7fdc84595e`
- Production records before V2: `0`
- Model outcomes before V2: `false`
- Reason: `PRE_GENERATION_SPECIFICATION_COHERENCE_FAILURE_FOUND_BY_STATIC_VALIDATION`

The V1 failure involved unbound c04/c09 constants and an identical c03 pair.
V2 resolves these prospectively without changing the task set, source classes,
panel counts, splits, model panel, estimand, or outcome routing.

## Frozen V2 decisions

- c04 `CONTEXT_PHRASE`: `in the presented example`
- c09 `CONTEXT_PREFIX`: `For context`
- c03 reference: `It is the case that {ARG_A} is {REL_LEX} {ARG_B}.`
- c03 realization: `{ARG_A} is {REL_LEX} {ARG_B}.`
- Duplicate rejection remains global for exact and normalized text; c03 has no exemption.
- Task slugs: `spatial`, `quantitative`, `mereological`.
- Generated spatial ordinal width: six decimal digits.
- Candidate selection: ascending SHA-256 under `PA-EXT-B-V1-ORDER`; task-specific lexical order cannot override selection.
- Final serialization: task slug, split, condition, family ID, record role.
- Quantitative pairs are globally unique. The frozen deterministic V2 construction is
  `A = 11 + ((global_index - 1) mod 22)` and
  `B = 4 - floor((global_index - 1) / 22)` for `global_index` 1..220.
  It preserves the inherited numeric domain and `A > B` relation while removing
  repeated numeric pairs.
- WordNet underscores become one ASCII space only in rendered surface text; source identity retains the original lemma form.

## Static closure and schemas

V2 freezes machine-readable construction, rendering, source-bank, record,
manifest, and provenance schemas. Every c01–c10 placeholder is bound; c03
reference and realization surfaces differ; no legacy `xa` condition is emitted.

The validator checks parent and V1 hashes, actual StepGame and WordNet source
hashes, source contracts, quantitative uniqueness, all condition closures,
identities, schema requirements, and the no-production/no-model boundary.

Synthetic tests cover rendering, c03 distinctness, constants, deterministic IDs,
six-digit formatting, hash ordering, quantitative uniqueness, canonical JSON,
schema rejection, and legacy-ID exclusion.

## Final amendment policy

After V2, one production construction attempt is allowed. If the frozen
construction cannot produce a valid three-of-three panel, EXT-B terminates at
the dataset-construction stage. Only a separately reviewed mechanical recovery
with unchanged V2 scientific bytes and rules may occur.

## V2 artifact hashes

| Artifact | SHA-256 |
|---|---|
| `paper_a_ext_b_construction_amendment_v2.json` | `f4aed55dff5ad0f690ade26aae35e2fd923944a598fd0871b5c076dfc0874988` |
| `paper_a_ext_b_construction_spec_v2.json` | `2344a45a1dff59af63fd8be96a890974b33722e09c7dad0807a4e1e214abee29` |
| `paper_a_ext_b_rendering_conditions_c01_c10_v2.json` | `dff800b21ac6e96db73724a48e32e8efeb66f210d2424e2869a6d8d7bc94ae13` |
| `paper_a_ext_b_source_bank_schema_v2.json` | `2ed4b9ccce0f25e7d1c060ed96e39c3c6be3c273de94b691a17168bd963b7989` |
| `paper_a_ext_b_record_schema_v2.json` | `c50544a29eb267fd5f46d50b07510015e9679b3a7263320e35c8c4ab54bf95eb` |
| `paper_a_ext_b_panel_manifest_schema_v2.json` | `1888ec78fb94275e38d8c383d9a3a426102e6fbca3bf08dc2600e10337148839` |
| `paper_a_ext_b_provenance_schema_v2.json` | `8a53460de279ac1b0371c272f0176ac5972a034e977e290bbb2f679710f37fc4` |
| `paper_a_ext_b_construction_binding_v2.json` | `03e53a9936452925ea3d8242246b05ea30bb422112d9b9ed20778bdcb0707ec7` |
| `validate_paper_a_ext_b_construction_v2.py` | `ee5b9c15f25240bd36b82e42d38b8b4e7e291f435bc768ad86dbe3aca663353a` |
| `test_paper_a_ext_b_construction_v2.py` | `f278ccb30bb41dacbd7da4c76ffb0c1945fbfd508d73db45fae1b4c9713a93e6` |

## Flags

```text
EXT_B_AMENDMENT_V2_CREATED=true
EXT_B_AMENDMENT_V2_PROSPECTIVE=true
EXT_B_AMENDMENT_V2_FINAL=true
EXT_B_PRODUCTION_RECORDS_BEFORE_V2=0
EXT_B_MODEL_OUTCOMES_BEFORE_V2=false
EXT_B_NO_FURTHER_SCIENTIFIC_AMENDMENT=true
EXT_B_NEXT_LIFECYCLE_ACTION=ONE_FINAL_DATASET_CONSTRUCTION_ATTEMPT_UNDER_V2
DATASET_GENERATED=false
MODEL_INFERENCE_RUN=false
HIDDEN_STATES_ACCESSED=false
MODEL_AUTHORIZATION_CREATED=false
SCIENTIFIC_RESULT_CREATED=false
TEMPORAL_RUNTIME_EXECUTED=false
```
