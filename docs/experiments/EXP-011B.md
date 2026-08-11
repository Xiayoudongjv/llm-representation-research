# EXP-011B Expanded Answer-Level Evaluation

## Research Question

Does the 24-item EXP-009 behavioral pattern remain stable on the larger,
quality-audited 80-item EXP-011 dataset?

## Motivation

EXP-009 used six items per group. EXP-011 provides 20 items per group, and
Tasks 022 and 023 improved semantic and scoring robustness before evaluation.

## Method

The experiment uses normal deterministic generation only. It does not apply
activation steering or hidden-state intervention.

## Dataset

The EXP-011 dataset has 80 deterministic short-answer items: 20 each for
logic, causality, analogy, and definition.

## Generation Configuration

The fixed prompt requests only a short answer. Generation uses `do_sample=False`
and `max_new_tokens=32`; the summary records the actual configuration.

## Scoring

Each answer is evaluated by `src.answer_scoring.score_answer` with the dataset's
`boundary_aware` scoring rule.

## Metrics

The experiment reports item-level correctness, overall and group accuracy, and
descriptive 95% Wilson confidence intervals.

## Results

Qwen/Qwen3-1.7B completed all 80 deterministic generations. Overall accuracy
was 0.650 (Wilson 95% CI: 0.541–0.745). Group accuracy was logic 0.700
(0.481–0.855), causality 0.600 (0.387–0.781), analogy 0.450 (0.258–0.658),
and definition 0.850 (0.640–0.948).

## Comparison with EXP-009

The summary records available EXP-009 group accuracy, EXP-011B group accuracy,
and group-level differences. Compared with EXP-009, logic changed by -0.133,
causality by -0.067, analogy by +0.117, and definition by +0.183. Analogy
remained the lowest-accuracy group, but the group ranking was not identical:
definition became the highest-accuracy group. A single comparison does not
establish stability.

## Limitations

- One model only.
- Twenty items per group remains modest.
- Short-answer task only.
- String and boundary scoring is not a semantic judge.
- Task groups are hand-designed.
- Normal generation only.

## Interpretation Rules

Allowed interpretations concern whether this behavioral baseline became more or
less stable, whether group rankings changed, and whether analogy remained a
difficult group. This experiment does not show that representation geometry
caused behavioral differences, that steering improves reasoning, or that the
model has intrinsic task modules.
