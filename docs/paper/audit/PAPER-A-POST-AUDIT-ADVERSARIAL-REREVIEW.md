# Paper-A Post-Audit Adversarial Rereview

Status: `PA_NOVELTY_003_POST_AUDIT_ADVERSARIAL_REREVIEW`
Scope: EXP-021 through EXP-027 only. EXP-028 excluded.
Reviewer stance: independent, hostile, prior-art-aware.

## 1. Primary Claim Validity

Frozen primary claim: `A preregistered three-model empirical dissociation of cross-depth fixed-readout compatibility dimensions: distance-associated structure is common, while source/target organization and simple recalibratability are not determined by that common structure.`

| Proposition | Verdict | Evidence basis |
| --- | --- | --- |
| P1: all three tested models show positive depth-distance-associated fixed-readout compatibility structure | SUPPORTED | Qwen, OLMo, Llama each `POSITIVE_SUPPORTED` |
| P2: three models do not share one source/target organization state | SUPPORTED | Qwen/Llama `TARGET_DOMINANT`; OLMo `SOURCE_DOMINANT` |
| P3: three models do not share one LOW-D recalibratability state | SUPPORTED | Qwen `NOT_SUPPORTED`; OLMo/Llama `SUPPORTED` |
| P4: models sharing source/target organization can differ in recalibratability | SUPPORTED | Qwen and Llama both `TARGET_DOMINANT`, but LOW-D differs |
| P5: first two-model pattern did not determine third-model outcome | PARTIALLY_SUPPORTED | Under the registered three-profile rule, Llama produced a third tuple; this is one prospective observation, not a trained predictor |
| P6: a single scalar distance/degradation description is insufficient in these models | SUPPORTED | Three dimensions produce non-identical tuples across models |

`PRIMARY_CLAIM_VALIDITY = NARROWED`

Safe ceiling: in the three tested models, the registered profiles are not reducible to the shared distance-support result. This is an empirical categorical observation, not statistical or causal independence.

## 2. Critical Logic Check

- Different observed tuples => independent mechanisms: `NOT_CLAIMED`
- Different tuples => statistical independence: `NOT_CLAIMED`
- Different models => architecture causality: `NOT_CLAIMED`
- Recalibration differences => different transport mechanisms: `NOT_CLAIMED`
- Distance association => universal depth law: `NOT_CLAIMED`

Maximum claim ceiling: `THREE_MODEL_EMPIRICAL_PROFILE_DISSOCIATION`, with no causal/statistical-independence extension.

## 3. Dissociation Strength

`DISSOCIATION_LEVEL = LEVEL_2`

Highest supported level: cross-model empirical dissociation between measured dimensions. LEVEL_3 statistical independence and LEVEL_4 causal independence are not supported.

## 4. EXP-027 Counterfactual Value

Without EXP-027, Qwen + OLMo would support a simple binary association: target-dominant with LOW-D unsupported versus source-dominant with LOW-D supported. Llama breaks that mapping by combining target dominance with supported LOW-D recovery.

`EXP027_SCIENTIFIC_ROLE = ESSENTIAL`

The prospective third-profile routing materially strengthens the inference; it is not merely a third post-hoc example.

## 5. SemRF Hostile Collision Review

Strongest accusation: `Paper A is SemRF plus renamed statistics and one extra model.`

| Dimension | Adjudication |
| --- | --- |
| Scientific object | PARTIAL_OVERLAP |
| Fixed-readout semantics | PARTIAL_OVERLAP |
| Source/target organization | PAPER_A_DISTINCT |
| Distance relation | PARTIAL_OVERLAP |
| Recalibration | PARTIAL_OVERLAP |
| Cross-model comparison | PAPER_A_DISTINCT |
| Joint profile | PAPER_A_DISTINCT |
| Dissociation | PAPER_A_DISTINCT |
| Prospective third-model adjudication | PAPER_A_DISTINCT |

`SEMRF_COLLISION_SEVERITY = MODERATE`

SemRF removes measurement-frame/drift novelty, but it does not reproduce the three-model registered profile dissociation.

## 6. Tuned Lens Collision Review

Known: layer-dependent mismatch, distance-associated transfer, learned translators. Not established by Tuned Lens: the fixed-readout source/target organization plus LOW-D recalibratability joint cross-model dissociation.

`TUNED_LENS_COLLISION_SEVERITY = MODERATE`

## 7. Patchscopes Collision Review

Patchscopes is not the central Paper-A contribution. Paper-A does not claim matrix construction itself; the remaining question is cross-model dimensional dissociation.

`PATCHSCOPES_COLLISION_SEVERITY = MINOR`

## 8. Post-Hoc Taxonomy Attack

- Distance dimension: historical but re-registered/formalized in EXP-026.
- Source/target organization: historical lineage; prospectively defined in EXP-026.
- Recalibratability: historical lineage; prospectively defined in EXP-026.
- Profile combination: registered.
- EXP-027 routing: prospectively frozen before outcome.

`POST_HOC_TAXONOMY_RISK = MODERATE`

## 9. Generalization Attack

The paper must not claim population-level generality. Safe scope: existence of multiple observed organizations among the three tested models and a within-set counterexample to a simple deterministic mapping.

`GENERALIZATION_LIMITATION = MODERATE`

## 10. Why-It-Matters Attack

The methodological implication is adequate but narrow: a single scalar degradation/transfer score can hide distinct measurement-frame organization and recalibratability properties.

`SIGNIFICANCE_CASE = ADEQUATE`

No safety, adapter, training, or industry benefit is claimed.

## 11. Measurement vs Mechanism Attack

The work is an empirical measurement contribution. Mechanism is not resolved. This is an expected scope limitation, not a fatal flaw.

`MECHANISM_LIMITATION = EXPECTED_SCOPE_LIMITATION`

## 12. Statistical Adequacy

- Depth-distance support: adequate for three models.
- SDI and LOW-D: adequate categorical adjudication.
- Bootstrap: registered one-sided cluster/percentile rules followed.
- EXP-027 routing: adequate.

No central claim should exceed the categorical empirical level.

## 13. Construct Redundancy Review

The Llama profile shows SDI and LOW-D are not deterministically equivalent in the tested set: Qwen and Llama share SDI but differ LOW-D. This is empirical non-redundancy, not statistical independence.

`NONREDUNDANCY_CLAIM = SUPPORTED_AT_EMPIRICAL_LEVEL`

## 14. Early Experiment Motivation Review

EXP-017 through EXP-020 are legitimate ancestry only. EXP-020 same-family replication motivates the measurement concern but is not a Paper-A novelty result.

`EXP020_ROLE = USEFUL_MOTIVATION`

## 15. Claim-by-Claim Survival

| CLAIM_ID | SURVIVAL |
| --- | --- |
| FC-01 | BACKGROUND_ONLY |
| FC-02 | SURVIVES_WITH_NARROWING |
| FC-03 | SURVIVES_UNCHANGED |
| FC-04 | SURVIVES_UNCHANGED |
| FC-05 | SURVIVES_WITH_NARROWING |
| FC-06 | SURVIVES_UNCHANGED |
| FC-07 | SURVIVES_UNCHANGED |
| FC-08 | SURVIVES_UNCHANGED |
| FC-09 | SURVIVES_UNCHANGED |
| FC-10 | SURVIVES_UNCHANGED |
| FC-11 | SURVIVES_UNCHANGED |
| FC-12 | SURVIVES_UNCHANGED |
| FC-13 | SURVIVES_UNCHANGED |

`CORE_CLAIMS_SURVIVE = 12`
`CORE_CLAIMS_NARROWED = 1`
`CORE_CLAIMS_REMOVED = 0`

## 16. Prohibited-Claim Rereview

No accidental reintroduction of first/universal/independence/causality/information-disappearance/adapter-failure claims was found in the post-audit artifacts.

## 17. Paper-Level Novelty Verdict

`NOVELTY_VERDICT = MODEST_BUT_REAL_NOVELTY`

## 18. Scientific Value Verdict

`SCIENTIFIC_VALUE = USEFUL_EMPIRICAL_INSIGHT`

## 19. Venue Rereview

| Venue | Fit | Dominant weakness |
| --- | --- | --- |
| TMLR | PLAUSIBLE | significance |
| ICLR | BORDERLINE | novelty/breadth |
| ICML | BORDERLINE | mechanism |
| NeurIPS | BORDERLINE | significance/breadth |

## 20. Extension Reassessment

`PAPER_A_EXTENSION_REQUIRED = false`

The narrowed standalone contribution survives hostile review. No new experiment is needed for viability.

## 21. Final Standalone Decision

`FINAL_STANDALONE_DECISION = STANDALONE_VIABLE_BUT_HIGH_RISK`

The paper can survive as a narrow empirical measurement study, but it remains high-risk on significance and breadth.

`PAPER_A_MANUSCRIPT_RESUME_ALLOWED = true`

## 22. Final Flags

- `PA_NOVELTY_003_STATUS = COMPLETE`
- `PRIMARY_CLAIM_VALIDITY = NARROWED`
- `DISSOCIATION_LEVEL = LEVEL_2`
- `EXP027_SCIENTIFIC_ROLE = ESSENTIAL`
- `SEMRF_COLLISION_SEVERITY = MODERATE`
- `TUNED_LENS_COLLISION_SEVERITY = MODERATE`
- `PATCHSCOPES_COLLISION_SEVERITY = MINOR`
- `POST_HOC_TAXONOMY_RISK = MODERATE`
- `GENERALIZATION_LIMITATION = MODERATE`
- `SIGNIFICANCE_CASE = ADEQUATE`
- `MECHANISM_LIMITATION = EXPECTED_SCOPE_LIMITATION`
- `NONREDUNDANCY_CLAIM = SUPPORTED_AT_EMPIRICAL_LEVEL`
- `NOVELTY_VERDICT = MODEST_BUT_REAL_NOVELTY`
- `SCIENTIFIC_VALUE = USEFUL_EMPIRICAL_INSIGHT`
- `PAPER_A_EXTENSION_REQUIRED = false`
- `IF_REQUIRED_MINIMUM_GAP = NONE`
- `FINAL_STANDALONE_DECISION = STANDALONE_VIABLE_BUT_HIGH_RISK`
- `PAPER_A_MANUSCRIPT_RESUME_ALLOWED = true`
- `PAPER_A_MANUSCRIPT_MODIFIED = false`
- `NEW_EXPERIMENT_PERFORMED = false`
