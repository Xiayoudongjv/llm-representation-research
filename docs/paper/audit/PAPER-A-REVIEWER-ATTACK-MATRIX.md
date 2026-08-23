# Paper-A Reviewer Attack Matrix

Status: `PA_NOVELTY_003_REVIEWER_ATTACK_MATRIX`
Scope: hostile post-audit rereview of the narrowed Paper-A story.

| ATTACK | SEVERITY | WHAT EXISTING EVIDENCE ANSWERS | RESIDUAL RISK |
| --- | --- | --- | --- |
| ATTACK_1: This is SemRF/Tuned-Lens/Patchscopes under new terminology | MODERATE | The prior-art audit concedes fixed-readout and measurement-frame novelty; the surviving claim is a registered three-model cross-dimensional profile dissociation not reproduced by those works | SemRF remains close; the paper must explicitly differentiate or reviewers may still see relabeling |
| ATTACK_2: The profile is merely a post-hoc taxonomy | MODERATE | EXP-026 registered SDI/LOW-D/distance definitions, and EXP-027 routing was frozen before outcome; not all dimensions were prospective, but the critical third-model adjudication was | Earlier historical/exploratory lineage remains visible and must be disclosed |
| ATTACK_3: Three models are insufficient for generalization | MODERATE | The paper does not claim population generalization; it claims a within-set empirical dissociation and a counterexample to a simple mapping | Significance is bounded; venue fit suffers |
| ATTACK_4: The distinction has no demonstrated practical consequence | MAJOR_BUT_ADDRESSABLE | The paper supports a methodological implication: scalar degradation/transfer scores can hide distinct measurement-frame organization and recalibratability | No direct adapter, safety, or deployment consequence is demonstrated |
| ATTACK_5: The statistics describe heatmaps but do not reveal mechanism | EXPECTED_SCOPE_LIMITATION | The paper is explicitly empirical/measurement-level; mechanism is left open and not claimed | Mechanism-oriented venues will see this as a limitation |

## Required Adjudication Flags

- `ATTACK_1_SEVERITY = MODERATE`
- `ATTACK_2_SEVERITY = MODERATE`
- `ATTACK_3_SEVERITY = MODERATE`
- `ATTACK_4_SEVERITY = MAJOR_BUT_ADDRESSABLE`
- `ATTACK_5_SEVERITY = EXPECTED_SCOPE_LIMITATION`
- `NO_FATAL_ATTACK_IDENTIFIED = true`
- `NO_NEW_EXPERIMENT_PROPOSED = true`
