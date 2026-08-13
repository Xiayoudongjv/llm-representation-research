# EXP-020 Preregistration: Qwen3-4B Representation Replication

## Model and Hardware Qualification

The exact model is `Qwen/Qwen3-4B`; no Qwen3.5, Instruct-2507, revision, or
architecture substitution is permitted. Before formal execution, the hardware
qualification record must freeze the revision, configuration, tokenizer
configuration, Transformers/Torch/CUDA versions, block count, hidden size, and
the first workable native/offloaded/4-bit mode.

## Data and Split Freeze

The existing EXP-018 controlled task prompt design is reused where compatible.
Before the formal run, exact fit/eval prompt IDs, task labels, transitions,
split seed, prompt-file hashes, and any tokenizer/chat-format compatibility
adjustment will be recorded. No semantic prompt revision or post-result prompt
filtering is permitted.

## Frozen Conditions

Direction construction uses FIT prompts only; evaluation uses held-out EVAL
prompts only. Conditions are `TASK`, `MATCHED_RANDOM`, and `OPPOSITE`.
Primary outcomes are held-out target-probe probability change, TASK minus
MATCHED_RANDOM, and TASK minus OPPOSITE. Centroid distance is not primary;
RSM/IVS are descriptive only.

## Layer and Beta

After configuration loading, block indices are mapped deterministically as
`round(fraction * (num_blocks - 1))`: primary depth 0.50 and secondary
descriptive depth 0.75. The primary 0.50-depth block at beta 0.75 alone
determines the representation gate. Beta 0.50 is optional descriptive only;
no layer or beta search, beta 1.0, adaptive beta, or per-task optimization is
allowed.

## Representation Gate

Report paired mean and median differences, bootstrap 95% confidence intervals,
and paired sign proportions using seed 20260812. The primary gate requires all
of: clear-majority held-out TASK target-probability increases; positive mean
TASK change; positive primary TASK-minus-MATCHED_RANDOM comparison; and
positive primary TASK-minus-OPPOSITE comparison. The only labels are
`REPRESENTATION_REPLICATION_SUPPORTED` and
`REPRESENTATION_REPLICATION_NOT_SUPPORTED`; a secondary layer or beta cannot
rescue failure.

## Behavior Stop Rule

Behavior runs only if the primary representation gate is supported. Otherwise
record `BEHAVIOR_NOT_RUN_BY_PREREGISTERED_STOP_RULE`. If permitted, frozen
conditions are `NO_INTERVENTION`, `TASK_REAL`, `MATCHED_RANDOM`, and
`OPPOSITE`, at the same primary block and beta 0.75. Outcomes are frozen
task-answer correctness where applicable, item-level disagreements, length,
and malformed/empty/repetition diagnostics. The failed EXP-019 evaluator is
not a confirmatory behavioral metric.

## Status

No formal EXP-020 results are produced by this preregistration.
