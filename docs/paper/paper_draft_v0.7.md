# Paper Draft v0.7: Audit-Integrated Evidence Restructuring

*Provisional title: From Representation Shift to Behavioral Control: Auditing
Task-Associated Steering in LLM Hidden States*

## Central Narrative

This project studies task-associated hidden-state geometry and centroid-derived
steering in Qwen/Qwen3-1.7B and google/gemma-3-1b-it. Its contribution is an
evidence audit: initial controlled geometry, construction-coupling concerns,
held-out representation validation, relational-validation failure,
generation-time behavioral failure, and finally independent measurement
validation failure.

## Representation Evidence

EXP-003 and EXP-013 found related controlled geometry in Qwen and Gemma on a
small designed prompt set, with metric- and model-dependent peak depths. EXP-018
then used frozen fit/evaluation splits, a held-out probe, matched random, and
opposite controls. In that design, TASK increased target probe probability in
216 of 216 conditions and exceeded matched random and opposite controls. This
supports held-out target-directed representation movement, not behavioral task
conversion.

## Relational and Behavioral Limits

EXP-018 did not validate task-specific relational preservation against matched
random perturbations. EXP-017 found no stable TASK advantage over equal-norm
random perturbation in its frozen behavioral pilot. Those results limit claims
about relational invariants and task-specific behavioral control.

## Independent Behavioral Targetness Measurement Attempt

EXP-017 correctness alone could not determine whether generated outputs changed
task identity. We therefore preregistered an independent output-level task
classifier. Its development corpus performance was perfect, but the
construction audit had already identified lexical shortcut risk. A separately
constructed, human-reviewed, and frozen Final-200 set was then evaluated
exactly once using the frozen evaluator. Independent balanced accuracy was
0.4850 and macro F1 was 0.4580, below preregistered thresholds of 0.70 for both
metrics and 0.60 recall for every class. The evaluator therefore failed
independent generalization, so EXP-017 targetness analysis was not unlocked. No
post-hoc retraining, feature removal, threshold change, or replacement test set
was used to rescue the result.

This is a measurement-validation failure, not evidence that behavioral
targetness definitely did not change. It does show that the available frozen
evaluator cannot support a robust semantic targetness claim for EXP-017.

## Contribution

The contribution is not state-of-the-art steering performance. It is a methods
and evidence-audit study showing how apparently strong steering evidence
weakens as construction coupling, independent representation validation,
generation-time intervention, and independent measurement validation are
introduced sequentially. The positive representation-transition result remains
bounded; relational-specific, behavioral, and behavioral-targetness claims do
not survive the stronger checks.

## Limitations

The record involves two small models, hand-designed representation prompts, one
generation-time pilot, and one frozen independent evaluator test. It does not
establish reasoning improvement, semantic task conversion, safe steering, or a
universal representation-behavior theory.
