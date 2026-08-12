# EXP-019 Dataset Validity Audit

Status: `STRUCTURALLY_VALID / SCIENTIFIC_VALIDITY_UNDER_AUDIT`

Decision: `REQUIRES_DIVERSITY_REMEDIATION`

This audit is descriptive and read-only. It does not train the frozen
behavioral evaluator, inspect EXP-017 outputs, or modify the 760-row corpus.

## Protocol Compliance

- Counts, four-class family balance, split isolation, clear-label notes,
  length-band balance, and lexical-challenge counts: PASS.
- Multiple provenance categories: FAIL. All 760 records are transparently
  marked `rule_composed`.
- No single provenance domination: FAIL.
- Class-balanced provenance: PASS only within the single-source construction;
  it does not establish provenance diversity.
- Template/source diversity: PARTIAL. There are 60 template families and no
  template family occurs in only one split, but the templates remain
  deterministic and class-specific.

## Lexical and Template Findings

The strongest class-concentrated terms include `holds`, `rule`, `entails`
(logic); `mechanism`, `through`, `leads` (causality); `relation`,
`corresponds`, `connects` (analogy); and `is`, `object`, `role` (definition).
Several occur exclusively in one class. A three-marker dictionary learned
only from the training split reached balanced accuracy 0.8417 on validation
and 0.7000 on test, indicating substantial shortcut risk.

Content-family vocabulary overlap was low: mean shared-vocabulary/union
fraction was 0.1083, while mean class-specific vocabulary/union fraction was
0.1917. All 190 families had some shared vocabulary, but class-coded wording
often dominates the shared topic words.

All 60 template families covered at least two splits (44 covered all three;
16 covered two), so split-only template leakage was 0. This does not remove
within-template class leakage: each class has its own deterministic template
families and syntactic skeletons.

Length bands were balanced (252 short, 256 medium, 252 limited-long overall),
but the lexical shortcut risk is present in all bands, especially in short
responses. Human review is required for naturalness and task plausibility.

## Manual Audit and Naturalness

`manual_audit_review_sheet.csv` contains the frozen 76-example sample with
judgment columns intentionally blank. No human judgments were fabricated.
Transparent structural rules flagged repeated boilerplate, repeated class
specific skeletons, and exact phrase-frame reuse. No malformed-grammar count
was asserted as a human-quality judgment; manual review remains required.

## Decision and Remediation

The corpus is structurally valid but should not be called frozen or
evaluator-ready. The preferred remediation is Option A: retain the current
760 examples as a procedural development corpus and add an independently
authored or independently sourced evaluation set. Option B (replacing a
predeclared fraction of families) and Option C (training-only use with a
completely independent natural-language final test) are alternatives with
different cost and comparability tradeoffs.

The current evidence supports `REQUIRES_DIVERSITY_REMEDIATION`, not
`REQUIRES_MAJOR_RECONSTRUCTION`: the family/split structure is useful, but
provenance and lexical/template independence are insufficient for the sole
basis of the target-sensitive evaluator.

## Reproducibility Notes

The machine-readable details are in
`experiments/exp019/data/dataset_validity_audit.json`. The original dataset,
protocol, schema, split assignments, and acceptance criteria were unchanged.
