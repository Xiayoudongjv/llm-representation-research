# EXP-019 Gap-128 Construction Audit

This document records the offline construction and structural audit of the
128-candidate gap-filling pool for the procedural development corpus.

## Scope

- The 26 borderline corrected human-review candidates were excluded from the
  primary pool rather than automatically accepted or rewritten.
- The 128 gap candidates fill the class deficits left by the retained 72 rows.
- Candidate normalization receives only `candidate_id` and `raw_response`.
- No model, evaluator, EXP-017 output, or hidden-state/vector artifact is used.

## Targets

The gap targets are logic 42, causality 30, analogy 26, and definition 30.
The assembled pre-human-audit pool contains 200 rows, 50 per class. It is not
the final behavioral evaluator set: a 40-row human audit remains blank and
must be completed before any evaluation use.

## Provenance and sources

The gap pool records `independent_external`, `rule_composed`, and
`ai_assisted_surface_normalized` construction pathways. Source URLs are
recorded as provenance references; no fabricated URLs are used. The validator
checks that no provenance category exceeds 70%, each class uses at least two
categories, at least ten source references are present, and no external source
exceeds 15% of externally sourced candidates.

## Audit checks

The offline validators check IDs, class balance, normalization alignment,
surface-only status, duplicate normalized responses, length bands, lexical
marker summaries, and blank human-audit fields. Character TF-IDF similarity is
reported as a diagnostic only; no classifier is trained.

Run:

```text
python experiments/exp019/validate_gap128.py
python experiments/exp019/validate_final200_candidate_pool.py
```

The output is a pre-human-audit construction record, not a claim that the
corpus is evaluator-ready.
