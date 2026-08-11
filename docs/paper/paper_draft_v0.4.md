# Paper Draft v0.4

## Abstract

We study representation geometry, calibrated representation-level steering,
and a small behavioral baseline in Qwen/Qwen3-1.7B. Findings are exploratory:
they are limited to one model, hand-designed tasks, and descriptive metrics.

## Representation-Level Results

Earlier experiments found task-associated geometry and calibrated centroid
transitions at selected layers. These are representation-level observations,
not evidence of improved generation-time reasoning.

## Expanded Behavioral Evaluation

EXP-009 used only 24 items. EXP-011 expanded this to 80 hand-designed
short-answer items, underwent a semantic quality audit, and adopted
boundary-aware scoring. EXP-011B raw strict accuracy was 0.650. EXP-011C found
eight clear lexical or morphological scoring misses. EXP-011D patched only
those audit-approved equivalents and froze final behavioral accuracy at 0.750.

Final group accuracy was causality 0.950, definition 0.850, logic 0.750, and
analogy 0.450. The EXP-009 group ranking did not remain stable on the expanded
benchmark. Analogy remained the lowest-performing group in both evaluations.
This does not show that analogy is intrinsically harder, that representation
geometry explains the ranking, that causality ability is generally 95%, or that
the benchmark comprehensively measures reasoning.

## Representation-Behavior Link Discussion

EXP-010 used earlier small behavioral estimates and only four groups. It is
exploratory and partly superseded by the larger frozen EXP-011D baseline; its
n=4 correlations should not be emphasized. A future analysis may rerun the
link with EXP-011D metrics, but would remain underpowered with four groups.

## Limitations

The behavioral benchmark is hand-designed, uses finite acceptable answers, has
no independent human annotation or semantic judge, and covers one model. No
generation-time intervention has been evaluated.
