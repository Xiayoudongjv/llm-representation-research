# Paper-A Cross-Task Content Adversarial Review

Status: `PA_EXT_A_002_CONTENT_ADVERSARIAL_REVIEW`

This is a prospective adversarial attack review of the abstract panel content
design. It does not create real content or use model outcomes.

## Attack Table

| ID | Attack | Verdict | Mitigation |
| --- | --- | --- | --- |
| A1 | New task families are old classes under new names | MITIGATED | Each family has an explicit distinctness contract and forbidden relations; future validator checks class identity against old registry |
| A2 | New relations are lexical variants of old ones | MITIGATED | Relations are semantic-world relations disjoint from old logic/causality/analogy/definition; no paraphrase-only replication |
| A3 | Human authors choose easy examples | MITIGATED | Fixed-count direct authoring; no surplus; no model outcomes visible; objective validity rules |
| A4 | Reviewer discretion permits item shopping | MITIGATED | Review outcomes are coded; ambiguous items are excluded and logged |
| A5 | Task family encoded by vocabulary | MITIGATED | Multiple lexical realizations, shared vocabulary where possible, static vocabulary audit; residual structure documented |
| A6 | Class encoded by punctuation/syntax | MITIGATED | No punctuation-only rule; surface conditions balanced; future validator checks class-conditional surface counts |
| A7 | Source-family variants leak across FIT/DIAG/EVAL | MITIGATED | Source family never crosses partitions; validator checks isolation |
| A8 | Transformation families leak across partitions | MITIGATED | Transformation family is source-family scoped; validator checks isolation |
| A9 | Candidate surplus creates hidden selection | MITIGATED | `FIXED_COUNT_DIRECT_AUTHORING`; no surplus policy |
| A10 | Author writes toward old profile replication | MITIGATED | Author must not see old profiles, model outcomes, hidden states, or expected route |
| A11 | Historical item recurrence | MITIGATED | Future validator rejects exact/normalized text, source-family, semantic-source, and template recurrence |
| A12 | Length differences identify class | MITIGATED | Whitespace-token range `8..28`; class-conditioned length audit; no model tokenizer inclusion |
| A13 | Relation semantics ambiguous | MITIGATED | Each relation has validity and invalidity conditions; ambiguous items excluded |
| A14 | One task family structurally easier | MITIGATED | Inherent difficulty is documented, not selected; outcome-neutral balance; no model-guided difficulty matching |
| A15 | Manual raw-text injection bypasses generator | MITIGATED | Future generator accepts only contract-valid records with deterministic IDs |
| A16 | Runtime task/relation overrides | MITIGATED | Generator has no runtime override capability; static validator checks |
| A17 | Failed first panel replaced by second panel | MITIGATED | One-panel stopping rule; no replacement panel or source bank |
| A18 | Predictive EXP-024 rescue endpoint | MITIGATED | No predictive endpoint; EXP-024 remains negative |
| A19 | EXP-028 transformation science | MITIGATED | No T2/T1, DELTA_RM, DELTA_RO, operator complexity, or alignment endpoint |
| A20 | Not reproducible from documentation | MITIGATED | Machine-readable design, schema, deterministic IDs, SHA binding, and static validator |

## Verdict

- `ADVERSARIAL_DESIGN_REVIEW = PASS`
- `BLOCKING_ATTACKS_REMAINING = 0`

## Hard Flags

- `REAL_EXT_A_SOURCE_BANK_CREATED = false`
- `REAL_EXT_A_PANEL_CREATED = false`
- `REAL_EXT_A_CANDIDATE_ITEMS_CREATED = false`
- `REAL_EXT_A_MODEL_INFERENCE_PERFORMED = false`
- `REAL_EXT_A_RESULTS_CREATED = false`