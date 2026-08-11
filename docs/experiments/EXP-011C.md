# EXP-011C Expanded Answer Scoring Audit

## Motivation

EXP-011B uses 80 quality-audited short-answer prompts, but finite acceptable
answer lists can still miss direct lexical variants.

## Inputs

The audit reads EXP-011B answer results and the EXP-011 dataset. It does not
run or load a model.

## Audit Protocol

Each item receives exactly one of: strict_correct, likely_correct_scoring_miss,
partially_correct, ambiguous, or likely_wrong.

## Conservative Correctness Rule

Only direct lexical, morphological, or harmless-wording equivalents count as a
likely_correct_scoring_miss. Related concepts and alternate analogy relations
do not automatically count as correct.

## Metrics

Strict accuracy uses only strict_correct. Conservative audited accuracy adds
likely_correct_scoring_miss. The review ceiling additionally includes partial
and ambiguous labels; it is not accuracy or final correctness.

## Results

The offline audit retained 52 strict_correct labels, identified 8
likely_correct_scoring_miss labels, and assigned 7 partially_correct, 3
ambiguous, and 10 likely_wrong labels. Strict accuracy was 0.650; conservative
audited accuracy was 0.750. The 0.875 review ceiling is an uncertainty ceiling,
not accuracy or final correctness.

At group level, strict versus conservative audited accuracy was logic
0.700→0.750, causality 0.600→0.950, analogy 0.450→0.450, and definition
0.850→0.850. Eight direct lexical or wording equivalents are recommended for
future acceptable-answer review. Strict scoring therefore appears materially
brittle under the predefined threshold, especially for causality wording.
The conservative ranking changes from definition > logic > causality > analogy
to causality > definition > logic > analogy.

## Comparison with EXP-009B

EXP-009B reported strict accuracy 0.625, audited upper bound 0.625, and no
likely_correct_scoring_miss. Any comparison remains cautious because the
datasets and audit conditions differ.

## Limitations

- No independent human annotator.
- Rule-based/manual conservative audit.
- Finite acceptable-answer vocabulary.
- No semantic judge.
- Some answers remain interpretation-sensitive.

## Interpretation

This audit tests scoring robustness, not model reasoning quality.
