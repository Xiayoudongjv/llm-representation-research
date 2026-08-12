# EXP-017 Post-Audit Preregistration Amendment V1

## Status and Scope

This amendment freezes the first EXP-017 behavioral pilot after Research Audit
v1 and EXP-018. It is written before any official EXP-017 behavioral run. It
does not replace or edit the historical preregistration
[`EXP-017-PREREGISTRATION.md`](EXP-017-PREREGISTRATION.md) or its historical
condition file. The executable frozen specification is
[`intervention_conditions_v2.json`](../../experiments/exp017/intervention_conditions_v2.json).

This is a narrow generation-time intervention test, not a claim about
reasoning improvement, task conversion, safe steering, validity optimization,
or layer comparison.

## Evidence Requiring the Amendment

The original EXP-017 preregistration predates Research Audit v1 and the
independent EXP-018 validation. Audit v1 found that historical centroid
steering and nearest-centroid evaluation were construction-coupled, and that
RSM/IVS could remain favorable under common translation rather than providing
task-specific relational evidence.

EXP-018 subsequently found `transition_validation = PASSED` and
`relational_validation = FAILED`. Thus the Qwen L16 task-associated transition
direction has independent representation-level support, whereas RSM/IVS-based
"safe" and "validity" labels do not. The original L4 and L28 conditions are
therefore deferred rather than treated as safe or validity conditions in this
first behavioral pilot.

## Frozen Question, Model, and Data

**Question.** Does an independently validated Qwen L16 task steering direction
produce generation-time behavioral effects that differ from matched-norm random
and opposite-direction controls?

The model is only `Qwen/Qwen3-1.7B`. The study reuses the frozen 80-item
EXP-011D behavioral benchmark unchanged: prompts, expected answers, acceptable
answers, boundary-aware scoring, and the concise-answer prompting path are all
preserved. Generation is deterministic (`do_sample=False`, `max_new_tokens=32`)
with the same tokenizer and model. No sampling temperature or LLM judge is
used.

## Frozen Directions and Fit-Data Independence

The retained symmetric transition subset is:

- logic → causality
- causality → logic
- analogy → definition
- definition → analogy

Each behavioral item receives only the direction predefined for its source
group. A steering direction is fit only from the 24 controlled EXP-003 prompts:
for each group, Qwen L16 last-token representations are collected for all six
controlled prompts (three original-style and three paraphrases), and their
arithmetic mean is the group centroid. For source → target,
`delta_task = centroid_target - centroid_source`, without normalization.

No behavioral benchmark prompt, answer, generated output, score, or label may
contribute to centroid fitting. This preserves the independence of delta
construction from behavioral evaluation.

## Official Conditions

Only four conditions are frozen for the first pilot.

| Condition | Layer | Beta | Vector |
|---|---:|---:|---|
| `NO_INTERVENTION` | — | 0.00 | none |
| `TASK_REAL` | 16 | 0.75 | `delta_task` |
| `MATCHED_RANDOM` | 16 | 0.75 | deterministic equal-norm random vector |
| `OPPOSITE` | 16 | 0.75 | `-delta_task` |

The random-control seed is `20260317`. One deterministic random direction is
drawn per directed transition, L2-scaled exactly to that transition's task
delta, and reused for every matching behavioral item and all generation steps.
It must not be regenerated per question or token.

## Validated Hook Semantics

Task 042 recorded `HOOK_DIAGNOSTIC_PASS` for
`model.model.layers[16]` (`Qwen3DecoderLayer`). Its output is a rank-3 tensor.
The hook adds the selected vector only to `hidden_states[:, -1, :]` after the
block and before the next block. It acts once on the final prompt token during
prefill and once on the current new token during each cached decode forward;
it does not retroactively modify KV-cache states. A zero-vector hook was
exactly behavior-neutral and hook removal restored baseline generation.

## Outcomes and Comparisons

The primary outcome is source-task answer accuracy, reported by condition and
source group, with change from `NO_INTERVENTION`. Lower source accuracy alone
is not target conversion.

The primary causal comparison is `TASK_REAL` versus `MATCHED_RANDOM`. Secondary
comparisons are `TASK_REAL` versus `OPPOSITE` and versus `NO_INTERVENTION`. The
existing collateral diagnostics remain: output-token count, empty-answer rate,
consecutive exact-repetition rate, and malformed/non-short-answer rate under
the original fixed heuristic.

## Claim Boundary and Stop Rule

If the task vector changes accuracy more than the equal-norm random control,
the allowed claim is only: “generation behavior is causally sensitive to the
independently validated task-associated steering direction.” It does not show
that a task representation was converted, reasoning improved, the model became
causal or logical, or safe steering was validated. A separate target-sensitive
behavioral metric would be required for target-task conversion.

After this pilot, proceed only if the hook remains technically valid, the TASK
condition differs meaningfully from matched random, and an effect is not
dominated by malformed outputs or generic degradation. If TASK behaves like
RANDOM, record a negative result and pause. No additional layers or betas are
automatically added.

## Deferred Historical Conditions

L4 at beta 1.0 is deferred: its former mean-safe label is no longer supported
by independent RSM validation. L28 at beta 1.0 is also deferred: its former
validity-layer label remains exploratory and is not independently validated.
Neither is deleted as a historical idea; either may return only in a later,
separately preregistered layer-behavior study.
