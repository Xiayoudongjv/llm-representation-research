# EXP-019 Existing-100 Response/Card Alignment Audit

## Motivation

The existing-100 reaudit showed an anomalous retention pattern: 8/25 logic, 20/25 causality, 0/25 analogy, and 0/25 definition. This audit tests whether that pattern reflects response quality or an engineering alignment error between the Word response order and source-card metadata order.

No evaluator result, classifier prediction, model run, or EXP-017 output was used.

## Current Mapping

The Word response source is `C:\Users\Xiayo\Desktop\新建 Microsoft Word 文档 (2).docx`, which contains 100 nonempty paragraphs. The current map pairs paragraph position `n` with row `n` of `source_cards_100_simple.csv`.

The metadata file has four contiguous 25-item blocks:

- 1-25: logic
- 26-50: causality
- 51-75: analogy
- 76-100: definition

`source_cards_100_for_human.csv`, the earlier derived source-card file, matches the canonical card metadata row-for-row for ID, task class, topic group, source material, and source reference.

## Source-Response Correspondence

Correspondence asks only whether a response appears to have been written from its assigned source material. It uses shared entities, factual concepts, relation pairs, definitions, and mechanisms; it does not select a label based on what appears to fit best.

Under H0, the current positional map, counts are:

- `STRONG_MATCH`: 46
- `PARTIAL_MATCH`: 3
- `NO_MATCH`: 51

The 51 no-matches consist of one isolated logic response at position 3 and all 50 positions from 51 through 100. The three partial matches are positions 5, 25, and 49, where the response remains related to its card but is incomplete or less precise.

## Block-Order Hypotheses

Two deterministic hypotheses were compared:

- H0: current positional mapping.
- H1: retain positions 1-50 and swap metadata blocks 51-75 with 76-100.

H1 yields:

- `STRONG_MATCH`: 96
- `PARTIAL_MATCH`: 3
- `NO_MATCH`: 1

Small boundary offsets were not tested. H1 gives a complete one-to-one correspondence for positions 51-100, so there is no residual boundary pattern that justifies testing arbitrary offsets or permutations.

## Analogy/Definition Diagnostic

Positions 51-75 contain single-concept definitions in the exact order of definition cards 76-100: water cycle, evaporation, photosynthesis, tidal force, groundwater, momentum, and so on through chloroplast. Under the current pairing, those responses are compared to analogy relation pairs and all receive `NO_MATCH`.

Positions 76-100 contain two-relation correspondences in the exact order of analogy cards 51-75: whale flippers/human arms, well pump/irrigation pump, satellite sensor/tide gauge, and so on through immune barrier/physical barrier. Under the current pairing, those responses are compared to definition cards and all receive `NO_MATCH`.

After H1 swaps the two metadata blocks, all 50 positions receive `STRONG_MATCH`. This is direct source-material evidence of an engineering block-order mismatch, not a post-hoc interpretation of label appearance.

## Logic/Causality Diagnostic

The first 50 positions support the current mapping: 46 are `STRONG_MATCH`, 3 are `PARTIAL_MATCH`, and 1 is `NO_MATCH`. Thus the error is not a global 100-row offset. It is localized to the analogy/definition block order.

## Decision

**BLOCK_ORDER_MISMATCH_CONFIRMED**

The current metadata pairing is correct for positions 1-50. Positions 51-75 and 76-100 are assigned to the opposite metadata blocks. A simple deterministic block swap restores 50/50 strong source-response correspondence in that region.

## Correction Boundary

`existing100_alignment_correction_map.csv` records the 50 proposed engineering corrections. It maps each affected Word position to the source card it was evidently written from and gives a block-order basis. The map is not applied in this task: the Word source, canonical cards, and existing reaudit artifacts remain unchanged.

This is data-integrity repair, not response relabeling. The basis is the ordered source-material correspondence, not the claim that a response merely “looks more like” a different class.

## Impact on Existing Reaudit

The existing `existing100_audited_pool.csv` and `final200_rebalancing_plan.json` use the incorrect current mapping for positions 51-100. They are therefore **INVALIDATED_BY_ALIGNMENT_ERROR**. The previously reported 172-example remaining-gap estimate must not be used for collection planning.

After the correction map is explicitly approved and applied in a later task, the full Existing-100 reaudit and Final-200 plan must be recomputed from the corrected pairing. This audit does not apply that correction or generate replacement examples.
