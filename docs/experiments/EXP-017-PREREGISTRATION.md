# EXP-017 Generation-Time Intervention Pilot Preregistration

## Research Question

Does applying a previously derived task-transition steering vector during
autoregressive generation causally alter answer behavior? A secondary question
is whether representation-level control, mean-safe, and exploratory-validity
operating points differ in behavioral collateral damage. This pilot does not
test whether steering improves reasoning.

## Model

The sole pilot model is `Qwen/Qwen3-1.7B`. Qwen is selected because it has the
frozen, audited EXP-011D 80-item behavioral benchmark. Gemma is excluded from
this first behavioral pilot because it does not yet have an audited behavioral
baseline in this project.

## Frozen Data and Scoring

The pilot reuses `experiments/exp011/expanded_answer_prompts.json` and the
EXP-011D frozen benchmark definition without changing questions, expected
answers, acceptable answers, or scoring. Every item uses the existing
boundary-aware scoring rule.

## Frozen Conditions

The conditions are descriptive labels, not behavioral rankings.

| Condition | Layer | Beta | Rationale |
|---|---:|---:|---|
| `NO_INTERVENTION` | — | 0 | Deterministic frozen baseline. |
| `CONTROL_LAYER_REAL` | 16 | 0.75 | EXP-016 encoding/control operating point. |
| `MEAN_SAFE_LAYER_REAL` | 4 | 1.0 | Lowest mean IVS among threshold-eligible settings; minimum pair assignment was 0.667, so it is not called robust-safe. |
| `VALIDITY_LAYER_REAL` | 28 | 1.0 | EXP-016 exploratory validity/efficiency operating point. |
| Matched-norm random variants | matching real layer | matching real beta | Equal-norm generic-perturbation controls. |

All steering vectors are raw centroid differences; they are not normalized.
Their beta values and all condition details are frozen in
`experiments/exp017/intervention_conditions.json`.

## Frozen Transition Directions

Behavioral items use their known source group. Every source-group item receives
only its preassigned direction:

| Source group | Target group |
|---|---|
| logic | causality |
| causality | logic |
| analogy | definition |
| definition | analogy |

The direction is estimated before behavioral generation from EXP-003's unchanged
24 controlled prompts at the condition's layer:
`delta[source,target] = centroid_target - centroid_source`. This covers all four
groups using two bidirectional pairs, rather than applying one arbitrary
direction to every behavioral item.

## Critical Controls

`NO_INTERVENTION` is the zero-intervention control. Each real condition has a
matched-norm random-vector condition. The random vectors use base seed
`20260317`, are generated deterministically per layer and directed pair, and
are scaled to exactly the L2 norm of the corresponding real delta. The same
vector is reused for all matching behavioral items.

`CONTROL_LAYER_OPPOSITE` is additionally frozen for a 20-item subset: the first
five frozen IDs in each group (`001` through `005`). It uses `-delta` at layer
16 and beta 0.75. This subset and its IDs are enumerated in the JSON; it cannot
be enlarged based on observed behavior.

## Generation-Hook Semantics

The intended hook is the output of `model.model.layers[layer]`, after that
transformer block returns its hidden-state output and before the next
transformer block consumes it. The operation adds `beta * vector` only to
`hidden_states[:, -1, :]`.

During prompt prefill, it applies once to the final prompt-token block output
used for the first next-token prediction. During cached generation, it applies
on every decode forward to the sole newly processed last-token block output
used for the next prediction. Previously stored KV-cache entries and prior
token states are not modified retroactively.

Because a Transformers hook can be sensitive to a model's cache call pattern,
a separate implementation task must first validate this exact location and
prefill/decode behavior with a tiny diagnostic. It may not silently move the
hook elsewhere.

## Generation Settings

Generation will match EXP-011B as closely as technically possible:

- `do_sample=False`
- `max_new_tokens=32`
- the same concise answer prompt template
- the same Qwen tokenizer/model
- boundary-aware frozen scoring

No temperature sampling or LLM judge is allowed.

## Outcomes

The primary outcome is source-group answer accuracy and its change from
`NO_INTERVENTION`. Lower source accuracy alone is not evidence of successful
task conversion.

Collateral-damage outcomes are output token count, empty-answer rate,
consecutive exact-repetition rate, and malformed/non-short-answer rate. The
last rate uses the fixed heuristic: stripped answer is empty, contains a
newline, exceeds 12 whitespace tokens, or exceeds 160 characters. Repetition
is reported only as an exploratory adjacent-in-dataset-order normalized-output
rate within condition and source group.

The key task-directed comparison is each real condition against its matched-norm
random-vector control, rather than intervention versus no intervention alone.

## Safe-Layer Hypothesis

If representation-level relational preservation has behavioral relevance, the
mean-safe or validity operating point may show less behavioral degradation than
the control-layer condition at comparable intervention efficacy. This is a
hypothesis, not an expected outcome. Qwen L4's weaker pair-level robustness
requires cautious interpretation.

## Stop Rule

The pilot does not automatically expand. A larger study is considered only if
the hook operates as preregistered, effects are not obviously numerical or
artifact-driven, and either real steering differs meaningfully from matched-norm
random steering or the representation-derived operating points show
interpretable behavioral differences. If all interventions behave like random
perturbations, record the negative result and pause.

## Unresolved Implementation Risks

- Qwen's exact layer output tuple and KV-cache call pattern must be verified by
  the required tiny diagnostic.
- Hooking a cached decode path could produce a shape or device mismatch if the
  vector is not placed on the active tensor's device and dtype.
- Deterministic generation can still expose chat-template or special-token
  differences, so the EXP-011B prompt path must be reproduced exactly.
- The 80-item benchmark has finite acceptable answers; output changes must be
  separated from scoring artifacts using the predeclared collateral metrics.

## Interpretation Rules

Allowed conclusions are limited to whether this fixed generation-time
intervention changes behavior differently from matched-norm random
perturbation, and whether the preregistered operating points differ in
collateral outcomes. The pilot cannot establish reasoning improvement,
universal steering behavior, or a causal cognitive interpretation.
