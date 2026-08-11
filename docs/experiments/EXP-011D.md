# EXP-011D Behavioral Benchmark Freeze

## Motivation

EXP-011B strict scoring was materially brittle, and EXP-011C identified eight
clear lexical or wording scoring misses. The benchmark is corrected before
interpreting its behavioral baseline.

## Patch Rule

Only audit rows labeled likely_correct_scoring_miss with an explicit update
recommendation and a non-empty candidate answer are added.

## No Model Rerun

The model outputs are identical to EXP-011B. Only scoring vocabulary is
corrected offline.

## Results

Eight audit-approved additions were applied, and all 80 existing EXP-011B
answers were rescored offline. Final rescored accuracy was 0.750 (60/80),
exactly matching the EXP-011C conservative audited accuracy. Eight items
changed from incorrect to correct; no other labels were promoted.

## Final Behavioral Baseline

Final group accuracy was logic 0.750 (Wilson 95% CI: 0.531–0.888), causality
0.950 (0.764–0.991), analogy 0.450 (0.258–0.658), and definition 0.850
(0.640–0.948). The final ranking is causality > definition > logic > analogy.

## What Was Not Changed

- No semantic reinterpretation of ambiguous answers.
- No partial credit.
- No model regeneration.
- No intervention.

## Limitations

- Acceptable-answer sets remain finite.
- No independent human annotation.
- The short-answer benchmark remains hand-designed.
