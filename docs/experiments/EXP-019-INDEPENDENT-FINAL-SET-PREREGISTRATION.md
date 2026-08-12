# EXP-019 Independent Natural Final Evaluation Set

Status: preregistered design only. No final examples are created by this
protocol.

## Scientific Role

The existing 760-row corpus is a structurally balanced **procedural
development corpus**. It exhibits substantial template and lexical shortcut
risk and is not the frozen final behavioral evaluator dataset. It may support
development, training, and validation only.

The independent final set is the decisive evidence for evaluator validity. It
must be independent of the procedural templates, current content-family
generator, current marker vocabulary, classifier predictions, and EXP-017
steering outputs. The two datasets must not be merged.

## Frozen Size and Classes

The primary final set contains exactly 200 clear examples:

- 50 logic
- 50 causality
- 50 analogy
- 50 definition

Borderline and excluded candidates do not count. The set may not be reduced
below 200 without a documented amendment. A larger set is allowed only when
independent high-quality collection naturally produces it and the balance is
preserved.

## Provenance and Naturalness

At least two genuinely distinct provenance categories are required. The
preferred categories are `human_authored` and
`independent_educational_source`; `manually_adapted_external` may be used only
with explicit documentation. No provenance source may exceed 70% of the final
set, and no class may uniquely correspond to one provenance. The procedural
generator, current templates, a single LLM generator, and a single website or
source family may not be the sole source.

Responses must resemble plausible short human answers, be grammatically
natural, and be semantically interpretable. Repeated artificial class-coded
verbs and constructions such as “Routine light condition entails shines.” are
not acceptable.

## Output-Only and Length Requirements

The classifier receives only `response_text`. Each clear example must be
self-contained enough for a blinded reader to identify its dominant response
family without the original prompt. Bare “Yes.”/“No.” responses, isolated
nouns, pronoun-only references, and prompt-dependent fragments are excluded
unless independently judged clear.

The frozen bands remain short (1–5 tokens), medium (6–12), and limited-long
(13–20). Naturalness takes priority over exact one-third allocation. Per
class targets are approximately 25–35% short, 30–40% medium, and 25–35%
limited-long; no class may differ from another by more than 15 percentage
points in any band without documentation.

Topics must be neutral and diverse across classes. No class may be assigned a
single domain. Where feasible, topic domains should overlap across classes.

## Lexical and Template Independence

The following diagnostic markers are frozen for reporting, not as universal
forbidden words:

- logic: `holds`, `rule`, `entails`
- causality: `mechanism`, `through`, `leads`
- analogy: `relation`, `corresponds`, `connect`
- definition: `is`, `object`, `role`

The previously frozen explicit challenge markers are also reported:
`logic`, `logical`, `therefore`, `because`, `cause`, `causes`, `analogy`,
`analogous`, `define`, `definition`, `means`.

No class may be deliberately written around these markers. Their frequency
and class distribution must be reported in the independent set.

The final set must not reuse procedural `template_family` strings. Before
evaluation, run the preregistered exact duplicate, normalized duplicate,
repeated three-word prefix, character n-gram similarity, and TF-IDF nearest
neighbor audits against the procedural corpus. Thresholds and decisions must
be fixed before inspecting final classifier results; no post-hoc threshold
tuning is allowed.

## Labeling and Human Audit

Every candidate records `intended_task_class` and `label_quality`, where the
allowed values are `clear`, `borderline`, and `exclude`. Only clear examples
enter the primary set.

Before final freeze, a human reviewer audits at least 40 examples (20% of the
primary set), with the full 200 preferred. The reviewer sees response text
and proposed task class, but not classifier predictions, EXP-017 conditions,
or steering results. The audit records task-label agreement, naturalness,
lexical giveaway, self-containedness, and ambiguity. Ambiguity and
naturalness rates must be reported.

## Frozen Classifier Acceptance

The existing procedural test and challenge metrics remain descriptive Tier 1
development robustness evidence and are not removed.

The independent final set is Tier 2 and is decisive. Before viewing its
results, the primary classifier and hyperparameters must already be frozen.
The primary one-shot acceptance criteria are:

- balanced accuracy >= 0.70
- macro-F1 >= 0.70
- recall >= 0.60 for every class

The independent final set is evaluated exactly once for the primary frozen
model. It must not be used for hyperparameter tuning.

If the procedural evaluator passes but the independent final set fails:
`evaluator_status = FAILED_INDEPENDENT_GENERALIZATION`, and EXP-017 remains
locked. If the independent set passes: `evaluator_status =
ACCEPTED_FOR_EXP017_TARGETNESS_EVALUATION`; only then may EXP-017 outputs be
opened for targetness scoring.

## Frozen Conditions and Scope

The machine-readable conditions are in
`experiments/exp019/independent_final_set_conditions.json`. The CSV template
is header-only. This task creates no examples, trains no evaluator, runs no
model, and does not inspect EXP-017 outputs.
