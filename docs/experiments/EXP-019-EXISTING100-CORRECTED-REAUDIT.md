# EXP-019 Existing-100 Corrected Reaudit

## Alignment Error

Task 058 confirmed a metadata block-order error. The Word response blocks are logic (1-25), causality (26-50), definition (51-75), and analogy (76-100), while `source_cards_100_simple.csv` stores analogy at 51-75 and definition at 76-100. The previous 28-retained / 172-gap audit used the incorrect pairing and is invalidated.

## Engineering Repair

The only repair authority was `existing100_alignment_correction_map.csv`. Positions 1-50 retain the current mapping. Positions 51-100 use the confirmed block swap only. The original Word document, canonical source cards, and historical audit files were not overwritten.

## Corrected Mapping Validation

The corrected mapping contains 100 positions and 25 candidates per corrected task class. Independent source-response correspondence gives:

- `STRONG_MATCH`: 96
- `PARTIAL_MATCH`: 3
- `NO_MATCH`: 1

This reproduces the Task 058 evidence pattern. The corrected class is taken from repaired metadata, never inferred from response wording.

## Reaudit Rules

The Existing-100 audit reused the same conservative statuses and frozen task definitions: `ACCEPT_AS_IS`, `ACCEPT_SURFACE_NORMALIZED`, `HUMAN_REVIEW`, and `REJECT`. Only grammar, word order, articles/prepositions, number, punctuation, duplicated wording, and awkward literal phrasing are eligible for surface normalization. No new facts, mechanisms, premises, analogy relations, definition properties, or certainty changes were added. Human-review rows were not rewritten.

The unchanged positions 1-50 retain their historical audit decisions. The repaired positions 51-100 were audited under their corrected source-card classes: definition responses were assessed as definitions, and relation-pair responses were assessed as analogies.

## Corrected Audit Results

Across all 100 corrected candidates:

- `ACCEPT_AS_IS`: 63
- `ACCEPT_SURFACE_NORMALIZED`: 9
- `HUMAN_REVIEW`: 26
- `REJECT`: 2

By class:

| Class | Accept as is | Surface normalized | Human review | Reject | Retained |
| --- | ---: | ---: | ---: | ---: | ---: |
| logic | 6 | 2 | 15 | 2 | 8 |
| causality | 13 | 7 | 5 | 0 | 20 |
| analogy | 24 | 0 | 1 | 0 | 24 |
| definition | 20 | 0 | 5 | 0 | 20 |

## Retained Pool

The corrected retained pool contains 72 candidates: logic 8, causality 20, analogy 24, and definition 20. This is the official retained count for planning; human-review candidates are not included.

The corrected retained topic distributions are:

- Logic: physics 3, earth science 3, biology 2.
- Causality: earth science 7, physics 5, biology 5, technology 2, general science 1.
- Analogy: biology 8, earth science 8, technology 4, physics 3, general science 1.
- Definition: biology 6, technology 6, earth science 4, physics 3, general science 1.

## Human Review Pool

There are 26 human-review candidates: logic 15, causality 5, definition 5, and analogy 1. The human decision and final-response fields are blank. The planning-only best case, if every human-review item were later accepted, is not treated as a scientific result.

## Rejections

Two candidates remain rejected, both in logic. They are preserved with reasons in `existing100_corrected_rejected.csv`. No corrected analogy or definition item was rejected merely because of its former, incorrect metadata block.

## Diversity Analysis

The corrected pool fixes the artificial analogy/definition inversion, but it does not make the pool fully diverse. Logic remains science-heavy and needs everyday, language, and quantitative rule applications. Causality contains repeated water, groundwater, tide, and related mechanisms, despite broader physics/biology/technology coverage. Analogy has all 24 retained items in the limited-long band and should add shorter and medium-length relational examples. Definition has 13 limited-long and 7 medium retained items and needs more varied length and non-science concepts.

Source references exist, but provenance categories are not recorded; the corrected outputs preserve `not_recorded` rather than fabricating provenance. Future additions should record provenance explicitly and avoid source concentration. Descriptive lexical checks show `not` as the most frequent non-stopword in retained logic, `water`/`causes` in causality, `water`/`system` in analogy, and `water`/`physical` in definition. The repeated three-word prefix `fin like limbs` occurs twice in retained analogy. Near-duplicate checks identify medium-risk clusters in causal water/groundwater/tide phrasing, analogy relation frames, and definition composition/containment frames; no high-risk pair is retained. No classifier was trained.

## Corrected Final-200 Gap

The scientific target remains 200 total, 50 per class. The official remaining workload is:

- Logic: 42
- Causality: 30
- Analogy: 26
- Definition: 30
- Total: 128

If all 26 human-review candidates were eventually accepted, the planning-only remaining workload would be 102: logic 27, causality 25, analogy 25, and definition 25. This best-case quantity must not replace the official retained count until human review occurs.

## Comparison with Invalidated Audit

The previous audit reported 28 retained and 172 remaining because positions 51-100 were paired with the opposite source-card blocks. Those values are `INVALIDATED_BY_ALIGNMENT_ERROR`. The corrected audit reports 72 retained and 128 official remaining. The difference is an engineering alignment repair, not post-hoc relabeling.

## Scientific Independence

The repair and reaudit were performed before evaluator training. No evaluator predictions were used, no model was run, and no EXP-017 output was opened or inspected.

## Remaining Collection Work

Collect only new, independently sourced candidates after human review, with priority on task clarity, semantic validity, naturalness, topic diversity, explicit provenance/source diversity, structural variety, and length balance. Do not restore the old mechanical topic quota or optimize future additions for classifier accuracy.
