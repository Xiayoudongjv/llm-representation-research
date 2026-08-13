# EXP-021 Preregistration: Downstream Persistence

## Scope

EXP-021 is a descriptive/causal-mechanistic follow-up, not a claim that later
layers correct or compensate for a steering intervention. Its primary model is
Qwen/Qwen3-1.7B because it already has a validated representation effect and
lower compute cost. Qwen3-4B is optional only if EXP-020's primary gate passes
and runtime is practical.

## Conditions and Measurement

Use `BASELINE`, `TASK`, `MATCHED_RANDOM`, and `OPPOSITE`, with one intervention
at the frozen layer. Reuse independently frozen probe/evaluation machinery. Do
not fit a separate probe at each downstream layer to maximize separability. If
cross-layer probe validity is unavailable, stop and document it.

## Downstream Checkpoints

Map normalized depths deterministically using
`round(fraction * (num_blocks - 1))`: intervention layer, 0.625, 0.75, 0.875,
and final block. Checkpoints cannot be selected from observed trajectories.

For each downstream layer k, `effect_k = P_target(h_k_TASK) -
P_target(h_k_BASELINE)` and `task_specific_effect_k = effect_k -
random_effect_k`. Report means, medians, bootstrap 95% confidence intervals,
and individual transition traces. Descriptive labels may be `PERSISTS`,
`ATTENUATES`, `DISAPPEARS`, `REVERSES`, or `MIXED`.

## EXP-022 Boundary

EXP-022 is `CONDITIONAL_FOLLOWUP` only. No formal timing experiment may run
unless EXP-021 reveals a clear persistence or attenuation pattern whose
interpretation timing can discriminate.
