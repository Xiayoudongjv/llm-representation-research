# EXP-024 Independent Dataset Review

Status: `DATASET_REPAIR_REQUIRED`

This is an independent read-only scientific review of the Task-097D-A
candidate dataset. The candidate, condition panel, protocol, schema, manifest,
and validator were not modified during this review.

## Review Identity

- Reviewer task: `097D-R`
- Review mode: read-only scientific audit
- Model/tokenizer/representation access: none
- Scientific outcome access: none
- Candidate modified: `false`

## Candidate Dataset Identity

- Path: `experiments/exp024/data/exp024_condition_panel_candidate.json`
- Reviewed SHA-256:
  `8583b57d9ed0ff98bd6d81eb3fc8f0f6c97a17d9acc63699b9d9b80e5c62eac5`
- Record count: `1760`
- Source-family count: `880`
- Condition count: `10`
- Semantic-class count: `4`

## Mechanical Verification

Reran:

```text
python experiments/exp024/validate_exp024_candidate_dataset.py
```

Result:

- `EXP024_SCHEMA_VALIDATION = PASS`
- `EXP024_MECHANICAL_VALIDATION = PASS`
- Exact text duplicates: `0`
- Normalized text duplicates: `0`
- Internal near-duplicate pairs at Jaccard `0.95`: `0`
- Historical exact reuse: `0`
- Historical direct paraphrase suspects: `0`

The mechanical validator passed, but mechanical validity is not sufficient for
scientific readiness.

## Pairing Structure

Protocol/schema require each source family to contain exactly one
`reference_form` and one `condition_realization`.

Verified:

- Every source family has exactly two records.
- Every family has one `reference_form` and one `condition_realization`.
- Family-level semantic class, condition, and partition are consistent.
- No third realization is present.

Verdict: `PASS`.

## Semantic-Class Review

A full family-level mechanical review was performed, supplemented by
deterministic rule-based semantic screening.

### Logic

A systematic subject-rule mismatch defect was found. The generator paired 55
subject phrases with four generic logical rules; many pairings are
semantically incompatible.

Examples:

- `exp024_c01_lexical_relex_FIT_logic_0218`: "a map without a scale bar meets
  the stated threshold"
- `exp024_c01_lexical_relex_FIT_logic_0050`: "a statement containing a hidden
  assumption has a unique identifier"
- `exp024_c01_lexical_relex_FIT_logic_0064`: "a database record without a
  unique key is in working condition"

Rule-based screening identified at least `146` logic reference families with
material subject-rule incompatibility. This is blocking because the controlled
`logic` class is not reliably valid.

### Causality

Most causality records follow plausible object/cause/effect pairings, but some
condition-specific realizations are grammatically broken under formal and
compressed transformations.

### Analogy

Most analogy records are interpretable. However, `6` reference families contain
a same-word pair, e.g.:

- `exp024_c02_syntactic_restructure_DIAGNOSTIC_analogy_0061`: "saw is to cut,
  drill is to drill"
- `exp024_c04_controlled_elaboration_EVAL_analogy_0145`: "ignition is to
  ignition, reflection is to image"

These are blocking for affected families.

### Definition

Many definition records have incorrect article agreement and/or broken
property phrasing.

At least `94` definition reference families contain patterns such as:

- "A observable language..."
- "a industry..."
- "a equation..."
- "A secondary industry is a industry..."

Some condition realizations further break grammar, for example:

- c03: "A formal garment is a garment with is defined by explicit rules."
- c06: "Observable equation: a equation with can be detected or measured."

This is blocking because the controlled `definition` class is not reliably
valid.

## Condition-by-Condition Review

| Condition | Fidelity verdict | Notes |
| --- | --- | --- |
| `c01_lexical_relex` | `PASS` as operation; base logic/definition defects remain | Lexical re-expression rule is followed, but underlying item validity is not cured. |
| `c02_syntactic_restructure` | `MODERATE_NONBLOCKING_LIMITATION` | Restructuring is applied, but definition article grammar and analogy same-word pair cases remain. |
| `c03_controlled_compression` | `BLOCKING_CONSTRUCT_DEFECT` | Compression produces missing subjects and `with is`-style broken phrases across logic/causality/definition. |
| `c04_controlled_elaboration` | `PASS` as operation; base logic/definition defects remain | Redundant elaboration is applied consistently, but cannot rescue invalid base content. |
| `c05_relation_explicit` | `PASS` as operation; base logic/definition defects remain | Explicit relation markers are inserted, but invalid base content remains. |
| `c06_relation_implicit` | `MODERATE_NONBLOCKING_LIMITATION` | Relation removal is applied, but some definition realizations are ungrammatical. |
| `c07_register_formal` | `BLOCKING_CONSTRUCT_DEFECT` | Formal shift is ungrammatical for logic and causality: "Should X is...", "Owing to X is...". |
| `c08_register_informal` | `PASS` as operation; base logic/definition defects remain | Informal shift is acceptable after the earlier duplicate correction. |
| `c09_neutral_distractor_prefix` | `PASS` as operation; base logic/definition defects remain | Neutral prefix is consistently applied. |
| `c10_anaphoric_reference` | `MODERATE_NONBLOCKING_LIMITATION` | Anaphora is applied, but analogy anaphora is ambiguous and definition article grammar remains. |

Counts:

- Conditions PASS: `5`
- Conditions moderate limitation: `3`
- Conditions blocking: `2`

## Condition Distinctness

The ten condition definitions remain distinguishable. No pair collapsed into
the same practical transformation.

- Collapsed condition pairs: `0`

## Condition-Class Interaction

Blocking interaction groups:

- `c03_controlled_compression` with `logic`: `22` families
- `c03_controlled_compression` with `causality`: `22` families
- `c03_controlled_compression` with `definition`: `22` families
- `c07_register_formal` with `logic`: `22` families
- `c07_register_formal` with `causality`: `22` families

Total blocking condition-class interactions: `5`.

## Partition Style Review

FIT, DIAGNOSTIC, and EVAL surface distributions are similar in the construction
report. No systematic partition-specific generation style was identified.

Verdict: `MINOR`.

The candidate uses one construction policy across partitions, but the
underlying class/condition semantic defects affect all partitions equally.

## Template Leakage Review

- Class-template leakage: `MODERATE`.
- Analogy-template status: `MODERATE_CONSTRUCT_INHERENT_TEMPLATE_LIMITATION`.

Class-specific templates are visible, but the more serious issue is semantic
invalidity, not only surface-template leakage.

## Four Existing Moderate Limitations

The construction report recorded four moderate limitations:

1. Synthetic slot-template construction.
2. Compressed analogy colon-notation concentration.
3. Systematic length differences for compression/elaboration.
4. Historical screen is mechanical rather than full semantic review.

Review:

- None of the four is upgraded to blocking by itself.
- They remain transparent limitations after repair.
- Upgraded to blocking: `0`.

## Diagnostic/EVAL Independence

Mechanical checks:

- DIAGNOSTIC and EVAL source-family overlap: `0`.
- No source-family sibling crosses partitions at the ID/base-identity level.
- No blocking semantic-sibling case detected by deterministic screen.

Verdict: `PASS` at the mechanical level.

## Cross-Condition Independence

Mechanical checks:

- No source family is reused across conditions.
- No forbidden base-content duplication was detected at the ID/base-identity
  level.
- Blocking cross-condition base-content cases: `0`.

## Historical Independence

Compared candidate text against available prior controlled dataset files from
EXP-017, EXP-018, EXP-019, EXP-020, and EXP-023.

- Historical exact reuse: `0`
- Historical direct paraphrase blockers: `0`
- Historical scenario reuse: not systematically established; the mechanical
  screen is not a complete semantic scenario audit.

## Primary Scientific Unit Assessment

The protocol's condition-level scientific unit remains conceptually defensible,
but the current candidate cannot support the intended inference because several
condition/class cells are not semantically valid.

Verdict: `LIMITED_BUT_DEFENSIBLE` at the protocol level; dataset repair is
required before use.

## Measurement Precision

Per condition/class:

- FIT: `6`
- DIAGNOSTIC: `8`
- EVAL: `8`

Condition totals:

- DIAGNOSTIC: `32`
- EVAL: `32`

Balanced-accuracy quantization is `1/32 = 0.03125`.

Verdict: `ADEQUATE`.

## Blocking Findings

Five blocking defect classes were identified:

1. `BLOCK-001`: systematic logic subject-rule semantic incompatibility.
   - At least `146` logic reference families affected.
   - Examples:
     - `exp024_c01_lexical_relex_FIT_logic_0218`
     - `exp024_c01_lexical_relex_FIT_logic_0050`
     - `exp024_c01_lexical_relex_FIT_logic_0064`
2. `BLOCK-002`: c03 compression grammar/coherence defects.
   - `66` families across logic, causality, and definition.
   - Examples:
     - `exp024_c03_controlled_compression_FIT_logic_0032`
     - `exp024_c03_controlled_compression_FIT_logic_0013`
3. `BLOCK-003`: c07 formal transformation grammar defects.
   - `44` families across logic and causality.
   - Examples:
     - `exp024_c07_register_formal_FIT_logic_0127`
     - `exp024_c07_register_formal_FIT_logic_0017`
4. `BLOCK-004`: definition article/property grammar defects.
   - At least `94` definition reference families affected.
   - Examples:
     - `exp024_c01_lexical_relex_FIT_definition_0093`
     - `exp024_c01_lexical_relex_FIT_definition_0059`
5. `BLOCK-005`: analogy same-word pair defects.
   - `6` analogy reference families affected.
   - Examples:
     - `exp024_c02_syntactic_restructure_DIAGNOSTIC_analogy_0061`
     - `exp024_c04_controlled_elaboration_EVAL_analogy_0145`

These are blocking because they undermine semantic-class validity and
condition-fidelity for a material subset of the controlled dataset.

## Nonblocking Limitations

- `EXP024_NONBLOCKING_LIMITATIONS = 4`
- The four existing construction limitations remain nonblocking after repair.
- No additional nonblocking limitation is added beyond the blocking defect
  classes above.

## Final Verdict

```text
EXP024_INDEPENDENT_REVIEW_VERDICT = DATASET_REPAIR_REQUIRED
```

The candidate dataset must not be frozen, and no model/tokenizer/representation
access should occur until a separate repair task corrects the blocking defects,
regenerates the candidate SHA, reruns mechanical validation, and receives a
focused rereview.

## Read-Only Guarantee

- `CANDIDATE_DATASET_MODIFIED = false`
- `CANDIDATE_MANIFEST_MODIFIED = false`
- `CONDITION_PANEL_SPEC_MODIFIED = false`
- `DATA_SCHEMA_MODIFIED = false`
- `PREREGISTRATION_DRAFT_MODIFIED = false`
- `VALIDATOR_MODIFIED = false`

Only this independent-review artifact and optional structured review artifact
were created.
