# STATUS: INVALIDATED_BY_ALIGNMENT_ERROR

Superseded by: `EXP-019-EXISTING100-CORRECTED-REAUDIT.md`

# EXP-019 Existing-100 Reaudit and Rebalancing Plan

## Motivation

The existing 100 responses are treated as a candidate pool, not as an automatically accepted evaluator dataset. This audit was completed before evaluator training and without accessing EXP-017 steering outputs. Its purpose is to protect task-class validity, semantic coherence, language quality, and independence of the future 200-example final set.

## Original Candidate Pool

The response-text source of truth is `C:\Users\Xiayo\Desktop\新建 Microsoft Word 文档 (2).docx`, which contains 100 nonempty paragraphs. Paragraph order maps one-to-one to the 100 rows of `experiments/exp019/data/source_cards_100_simple.csv`; the card file supplies candidate IDs, original task labels, topic-group metadata, and source references. The two files were not merged with any other candidate source.

The original distribution is balanced by assigned label: 25 logic, 25 causality, 25 analogy, and 25 definition. The source cards contain references but no provenance field; the audit therefore records provenance as `not_recorded` rather than inferring it.

## Audit Rules

Each candidate received exactly one disposition:

- `ACCEPT_AS_IS`: natural, self-contained, coherent, and clear for its frozen task class.
- `ACCEPT_SURFACE_NORMALIZED`: only a class-blind grammar or naturalness correction was made.
- `HUMAN_REVIEW`: a potentially salvageable item needs substantive human judgment; no replacement wording was generated.
- `REJECT`: the sentence is fundamentally mismatched, incoherent, incomplete, or would require new authorship to repair.

## Semantic Preservation

Only 9 items were surface-normalized. These corrections cover grammar, article/preposition usage, word order, terminology form, or redundant wording only. No new fact, mechanism, premise, analogy relation, defining property, or certainty change was introduced. All other non-retained items preserve their original response text; human-review rows have blank human-decision and final-response fields.

## Task-Class Audit

The largest finding is a label/function mismatch, not merely a language problem. The 25 assigned analogy items are predominantly single-concept definitions rather than two-relation correspondences. The 25 assigned definition items are predominantly relation comparisons rather than single-concept definitions. Their labels were not changed to save samples; all 50 were rejected because repair would require new content.

Within logic, 8 items were retained, 15 need human review, and 2 were rejected. The retained logic items mainly express exclusion, comparison, conditional conservation, or a rule/formula relation. Within causality, 20 items were retained and 5 need human review; the review items require technical qualification, term checking, or a substantive repair.

## Language/Naturalness Audit

The accepted pool excludes translation-like or incomplete wording unless a surface-only correction sufficed. Examples requiring human review include claims with unstated technical conditions, unclear literal translations, terminology requiring factual checking, and a causal sentence with no stated outcome. No automatic rewrite was made for those cases.

## Lexical Shortcut Audit

No classifier was trained or queried. Descriptive token, prefix, and character-n-gram checks show substantial class-linked vocabulary concentration:

- Logic: `water` (8) and `not` (6) are the strongest tokens; `not` and `without` are class-concentrated.
- Causality: `water` (9), `causes` (4), `changes` (4), and `momentum` (4) dominate; `water vapor` appears three times.
- Assigned analogy: `water` appears 15 times and `physical quantity` three times, but the deeper issue is that the text uses definitional frames rather than analogy relations.
- Assigned definition: `water` appears 17 times, `tidal bulges` appears three times, and the three-word prefix `fin like limbs` repeats twice; the deeper issue is relation-comparison framing.

The strongest same-class character-n-gram similarities include analogy items SRC-ANA-007/SRC-ANA-010 (0.5235) and causality items SRC-CAU-014/SRC-CAU-015 (0.4711). These are descriptive redundancy warnings, not model predictions.

## Topic Diversity

The initial pool is topic-concentrated. Assigned logic contains 13 earth-science items, 6 physics items, and 5 biology items; it has no everyday-life, language, mathematics, or social/general coverage. Assigned causality is broader but still science-heavy: 8 physics, 8 earth-science, 6 biology, and 2 technology items. The assigned analogy and definition sets also concentrate on water, biology, and physical-science concepts and cannot be retained because of task mismatch.

Among retained items, logic has 3 physics, 3 earth-science, and 2 biology examples. Causality has 7 earth-science, 5 biology, 5 physics, 2 technology, and 1 general-science example. The remaining collection should broaden topics rather than recreate the earlier five-topic-by-five-example structure.

## Provenance Diversity

All original response cards have a source reference, but no explicit provenance category. The audit preserves this absence as `not_recorded`. Retained logic draws from six source references, with the largest reference contributing 3/8 retained items (37.5%). Retained causality draws from 11 source references, with the largest references contributing 3/20 each (15%). Future collection must record provenance and avoid any single source or provenance category dominating a class.

## Length Distribution

The original classes have markedly different length distributions. Logic has 5 short, 18 medium, and 2 limited-long items; causality has 1 short, 19 medium, and 5 limited-long items; assigned analogy has 7 medium and 18 limited-long items; assigned definition has 25 limited-long items. The accepted logic pool has 1 short, 6 medium, and 1 limited-long item. The accepted causality pool has 1 short, 16 medium, and 3 limited-long items. Future additions should improve coverage without imposing an artificial exact balance.

## Retained Pool

The derivative audited pool contains all 100 originals. The retained candidate pool contains 28 items:

- 19 `ACCEPT_AS_IS`
- 9 `ACCEPT_SURFACE_NORMALIZED`

By frozen task label, retained counts are: logic 8, causality 20, analogy 0, and definition 0. This remains a candidate retained pool, not a frozen final dataset.

## Human Review Pool

Twenty items are in `existing100_human_review.csv`: 15 logic and 5 causality. The sheet leaves `human_decision` and `human_final_response` blank. Human review may accept, rewrite, or reject a candidate, but this audit does not auto-rewrite substantive issues or change labels.

## Rejections

Fifty-two items were rejected: 2 logic, 25 assigned analogy, and 25 assigned definition. Every rejected item is recorded in `existing100_rejected.csv` with its original text and a reason. No sample was silently dropped.

## Rebalanced Final-200 Plan

The scientific final target remains 200 accepted examples, with 50 per frozen task class. The current retained total is 28, leaving 172 future accepted examples:

- Logic: retain 8; collect 42 more. Prioritize everyday, language, and quantitative rule applications; make the logical operation explicit without relying on repeated `X is not Y` forms.
- Causality: retain 20; collect 30 more. Broaden beyond water, groundwater, and tide mechanisms; add diverse, documented everyday and social/general mechanisms.
- Analogy: retain 0; collect 50 new two-relation correspondences across several domains and sources.
- Definition: retain 0; collect 50 new self-contained single-concept definitions across several domains and sources.

For every class, collection priority is: task clarity, naturalness, semantic validity, topic diversity, provenance/source diversity, structural diversity, then length balance. The plan does not optimize for future evaluator accuracy.

## Scientific Independence

No evaluator was trained, no classifier predictions were used, no model was run, and no EXP-017 outputs were opened. The rebalancing plan is driven only by the prepared candidate pool, source-card metadata, and descriptive non-model lexical/redundancy checks.

## Remaining Work

Collect only new candidates that meet the frozen task-function definitions, carry explicit provenance/source metadata, and expand topic, source, structural, and length coverage. Re-run the same audit before any candidate enters the independent final-set collection process.
