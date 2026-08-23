# Paper-A Content Production Simplification Review

Status: `PA_EXT_A_002C_SIMPLIFICATION_REVIEW`

This is a prospective pre-data review. It does not create real semantic
assets, real source items, a real panel, model inference, results, or
authorization.

## 1. Problem

The V2 content-design route required:

`HUMAN_AUTHOR_880_SOURCE_FAMILIES -> deterministic transformation -> 1760 records`

That burden is high and introduces avoidable free-text discretion: author
fatigue, style drift, lexical drift, implicit difficulty drift, semantic
prototype bias, and partition-specific writing habits. Direct human authoring
is not automatically more scientifically valid than deterministic composition.

## 2. Candidate Routes

- `ROUTE_H`: retain 880 human-authored source families.
- `ROUTE_S`: structured semantic asset bank + deterministic composition +
  deterministic rendering.
- `ROUTE_M`: hybrid structured composition + small human semantic bank.

No additional route is introduced.

## 3. Task-by-Task Feasibility

| Task family | Classification | Validity by construction | Main risk |
| --- | --- | --- | --- |
| `exta_tf_spatial` | `COMPOSITIONAL_WITH_FROZEN_ASSET_BANK` | `HIGH` | relation vocabulary leakage |
| `exta_tf_temporal` | `COMPOSITIONAL_WITH_FROZEN_ASSET_BANK` | `HIGH` | causal reading drift |
| `exta_tf_quantitative` | `FULLY_COMPOSITIONAL` | `HIGH` | numeric marker leakage |
| `exta_tf_mereological` | `COMPOSITIONAL_WITH_FROZEN_ASSET_BANK` | `MODERATE` | part-whole mapping validity |

All four families can be produced without 880 item-level free-text authoring.
Mereological content requires a curated but reusable part-whole asset mapping;
this is still an asset-bank decision, not full-sentence authoring.

## 4. Scientific Validity Comparison

| Dimension | ROUTE_H | ROUTE_S | ROUTE_M |
| --- | --- | --- | --- |
| CROSS_TASK_INDEPENDENCE | STRONG | STRONG | STRONG |
| SEMANTIC_VALIDITY | ADEQUATE | ADEQUATE | ADEQUATE |
| OUTCOME_NEUTRALITY | ADEQUATE | STRONG | STRONG |
| LEXICAL_BALANCE | ADEQUATE | STRONG | STRONG |
| STYLE_CONFOUND_CONTROL | WEAK | STRONG | STRONG |
| REPRODUCIBILITY | ADEQUATE | STRONG | STRONG |
| HUMAN_DISCRETION | WEAK | STRONG | ADEQUATE |
| AUDITABILITY | ADEQUATE | STRONG | STRONG |
| NATURAL_LANGUAGE_QUALITY | STRONG | ADEQUATE | ADEQUATE |
| HISTORICAL_FRESHNESS | ADEQUATE | STRONG | STRONG |
| IMPLEMENTATION_COMPLEXITY | LOW | MODERATE | MODERATE |

Route S trades some natural-language fluency for reproducibility, lower
discretion, and validity by construction. That trade is scientifically
acceptable for this measurement-stability extension.

## 5. Route Decision

- `ROUTE_H_VERDICT = ELIGIBLE`
- `ROUTE_S_VERDICT = ELIGIBLE`
- `ROUTE_M_VERDICT = ELIGIBLE`
- `SELECTED_ROUTE = ADOPT_ROUTE_S`

Route M is not needed because every frozen family can be produced with a
frozen semantic asset bank. Adopting Route M would retain a partially free-text
path without a scientific necessity.

`SCIENTIFIC_INDEPENDENCE_PRESERVED = true`

Replacing 880 full-sentence human-authored families with structured semantic
assets plus deterministic composition does not weaken the claim ceiling:
profile stability across two independently designed task panels in the three
tested models. The new panel remains a distinct semantic/task universe and is
not generated from model outcomes.

## 6. Workload Estimate

| Burden type | ROUTE_H | ROUTE_S |
| --- | --- | --- |
| Free-text decisions | VERY_HIGH | VERY_LOW |
| Structured asset decisions | VERY_LOW | MODERATE |
| Relation rule decisions | LOW | MODERATE |
| Item-level reviews | ALL | ASSET_AND_RULE_LEVEL_ONLY |

Qualitative expected reduction: `APPROX_10X_OR_MORE` in free-text authoring
burden, without removing semantic safeguards.

## 7. Asset and Rule Governance

- Validate reusable semantic assets.
- Validate admissibility, composition, enumeration, and rendering rules.
- Use engineering sample inspection only if required.
- Do not manually approve all 1760 final sentences.

## 8. Old-Asset Reuse

- `OLD_ENGINEERING_ASSET_REUSE = ALLOWED` for normalization, deterministic ID
  construction, split allocation, serialization, validator patterns, and
  historical exclusion machinery.
- `OLD_SCIENTIFIC_CONTENT_REUSE = FORBIDDEN`.
- `OLD_CONTENT_AS_EXCLUSION_AUTHORITY = ALLOWED`.
- No old lexical/entity bank is assumed task-neutral enough for semantic-asset
  reuse without violating cross-task independence.

## 9. EXP-028 Boundary

- `EXP028_CODE_REUSE = NOT_NEEDED`
- `EXP028_SCIENTIFIC_CONTENT_REUSE = FORBIDDEN`
- EXP-028 remains untouched.

## 10. LLM and Model Firewalls

- `LLM_GENERATION_ALLOWED = false`
- No model inference, hidden-state access, embeddings, or classifier-guided
  selection.

## 11. Hard Flags

- `REAL_EXT_A_SEMANTIC_ASSET_BANK_CREATED = false`
- `REAL_EXT_A_SOURCE_BANK_CREATED = false`
- `REAL_EXT_A_PANEL_CREATED = false`
- `REAL_EXT_A_MODEL_INFERENCE_PERFORMED = false`
- `REAL_EXT_A_RESULTS_CREATED = false`
- `REAL_EXT_A_AUTHORIZATION_CREATED = false`
- `PAPER_A_MANUSCRIPT_MODIFIED = false`
- `EXP028_MODIFIED = false`