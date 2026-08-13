# EXP-020A Preregistration: Qwen3-4B Representation Replication

## Status and scope

EXP-020A is a confirmatory representation-level replication. Its scientific
status is `NOT_STARTED`. This document and
[`exp020_frozen_config.json`](../../experiments/exp020/exp020_frozen_config.json)
must be committed before any formal Qwen3-4B prompt is run. The protocol does
not inspect EXP-017 or EXP-019, generate behavior results, persist raw hidden
states, sweep layers or beta, change prompt semantics, or tune a probe after
evaluation performance is seen.

## Frozen model and execution environment

| Field | Frozen value |
|---|---|
| Model ID | `Qwen/Qwen3-4B` |
| Revision | `1cfa9a7208912126459214e8b04321603b3df60c` |
| Canonical path | `D:\Qwen3-4B-transfer` |
| Local loading | `local_files_only=True` |
| Config SHA-256 | `8ba006f74fecfaaeb392872a60f4a480e7ec9860153d2e1b769ec81f9a147f8a` |
| Architecture | `Qwen3ForCausalLM` / `qwen3` |
| Blocks / hidden size / vocabulary | 36 / 2560 / 151936 |
| Execution | native BF16 on `cuda:0` (`MODE_A_NATIVE`) |

The neutral local hardware qualification passed: peak forward GPU allocation
was 7.5339 GiB and the zero-intervention hook check passed with maximum logit
difference 0.0. This is an engineering check, not EXP-020A evidence.

## Explicit layer indexing

`block_index` always means the 0-based index in `model.model.layers`. With 36
blocks, the model returns 37 hidden-state entries: `hidden_states[0]` is the
embedding output, and `hidden_states[k + 1]` is the output after transformer
block `k`.

The sole mapping rule is `round(depth_fraction * (num_blocks - 1))`.

| Role | Depth | Block index | Corresponding hidden-state index |
|---|---:|---:|---:|
| Primary intervention / gate | 0.50 | 18 | 19 |
| Secondary descriptive robustness | 0.75 | 26 | 27 |

The future implementation must verify these indices against accessible module
hooks. No later remapping is allowed. The secondary block cannot rescue the
primary gate.

## Dataset and complementary split freeze

The study reuses the unchanged controlled dataset
`experiments/exp003/prompts_controlled.json` (SHA-256
`72dab733e6a1639dfc80d186f3af1dbce5c6d70da4905e6d6d422cf47064c472`).
The source split/transition conditions are
`experiments/exp018/validation_conditions.json` (SHA-256
`4ce4ebb1af318e7c25725980680c0dc62762e20790adcb7abf2026130f0d4169`);
the canonical hash for its groups, splits, and transitions is
`1aa1ae2aedb58e24c4c9672b60aaebdefaf9467fa4f0f18e2682bb956e583674`.

Groups are `logic`, `causality`, `analogy`, and `definition`. The two frozen
complementary splits are:

- A: original-style IDs 01–03 per group are FIT; paraphrase IDs 01–03 are
  EVAL.
- B: paraphrase IDs 01–03 per group are FIT; original-style IDs 01–03 are
  EVAL.

Each split has 12 FIT and 12 EVAL examples, all explicitly listed in the JSON.
FIT and EVAL IDs are disjoint within each split. The 12 ordered source-target
transitions are exactly all ordered pairs of distinct groups. This yields 72
paired held-out source evaluations across both splits (12 transitions × 3
source EVAL examples × 2 splits). No prompt filtering based on Qwen3-4B
outputs is allowed.

## Direction construction and conditions

At the primary block only, derive each direction from FIT representations:

`delta = target_centroid_fit - source_centroid_fit`.

No EVAL representation may influence a centroid, direction, scaler, or probe.
For each held-out source representation, use exactly these conditions:
`BASELINE`, `TASK`, `MATCHED_RANDOM`, and `OPPOSITE`.

`MATCHED_RANDOM` uses the EXP-018 procedure: standard-normal vector with base
seed 20260319 and `SeedSequence([20260319, 2, block_index, split_index,
source_group_index, target_group_index])`, scaled once to the matching task
direction's L2 norm and reused for all associated held-out source items.
`OPPOSITE` is `-delta`.

The primary beta is **0.75**. Beta 0.50 is secondary descriptive only; it
cannot rescue the primary result. No beta search, beta 1.0, adaptive beta, or
per-transition optimization is permitted.

## Independent probe

For each split, fit a model-specific measurement probe only on the 12 FIT
representations. The frozen pipeline is:

- `StandardScaler(with_mean=True, with_std=True)` fit on FIT features only;
- multinomial `LogisticRegression(solver="lbfgs", penalty="l2", C=1.0,
  max_iter=1000, class_weight=None, random_state=20260319)`; and
- fixed class order: `logic`, `causality`, `analogy`, `definition`.

The scaler and classifier are applied unchanged to all held-out conditions.
The probe is a measurement instrument, not the intervention definition; its
hyperparameters and preprocessing may not be tuned using EVAL performance.

## Outcomes, statistics, and primary gate

For paired held-out item `i`:

```text
task_effect_i     = P_target(TASK_i) - P_target(BASELINE_i)
random_effect_i   = P_target(MATCHED_RANDOM_i) - P_target(BASELINE_i)
opposite_effect_i = P_target(OPPOSITE_i) - P_target(BASELINE_i)
D_random_i        = task_effect_i - random_effect_i
D_opposite_i      = task_effect_i - opposite_effect_i
```

For `task_effect`, `D_random`, and `D_opposite`, report N, mean, median,
standard deviation, bootstrap 95% CI, and proportion greater than zero.
Bootstrap settings are frozen at seed 20260812 and 10,000 resamples. Aggregate
primary results are reported first, followed descriptively by source task,
target task, and transition pair; no favorable individual transition can
redefine success.

`REPRESENTATION_REPLICATION_SUPPORTED` applies only to primary block 18 at
beta 0.75 and requires all of:

1. mean `task_effect > 0`;
2. its mean bootstrap 95% CI excludes zero on the positive side;
3. mean `D_random > 0`;
4. its mean bootstrap 95% CI excludes zero on the positive side; and
5. mean `D_opposite > 0`.

Otherwise the result is `REPRESENTATION_REPLICATION_NOT_SUPPORTED`. A
technical validity failure before valid outcomes is
`REPRESENTATION_REPLICATION_INVALID`, distinct from scientific failure. There
is no historical 216/216 requirement and no secondary-layer rescue.

## Sanity checks and behavior boundary

Before a formal run, validate model revision, model config hash, prompt hash,
split/transition hash, block/hidden-state mapping, zero-hook equivalence,
beta, random seeds, and probe class order. Any mismatch stops the run.

EXP-020A has no behavior component. Only a supported primary representation
gate can authorize a separately preregistered EXP-020B. If the gate is not
supported, `EXP-020B behavior = NOT_RUN_BY_STOP_RULE`.

Even if supported, the allowable claim is limited to: “the held-out
target-directed representation transition replicated in Qwen3-4B under the
preregistered primary-layer protocol.” It does not support claims about scale
invariance, universal replication, behavioral control, reasoning improvement,
cognitive-space transformation, or true task manifolds.
