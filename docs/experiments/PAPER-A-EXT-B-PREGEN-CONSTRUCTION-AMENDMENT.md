# Paper A EXT-B Pre-Generation Construction Amendment V1

Status: `FROZEN_PRE_GENERATION_PRE_MODEL_OUTCOME`

This amendment resolves the first formal construction blocker before any EXT-B
record existed. It is a prospective protocol amendment, not an engineering
repair and not a response to model behavior.

## Provenance boundary

```text
AMENDMENT_REASON = FIRST_FORMAL_DATASET_CONSTRUCTION_ATTEMPT_BLOCKED_BEFORE_GENERATION_DUE_TO_UNBOUND_CONSTRUCTION_IDENTITIES
DATA_OBSERVED_BEFORE_AMENDMENT = false
GENERATED_RECORDS_BEFORE_AMENDMENT = 0
MODEL_OUTCOME_OBSERVED_BEFORE_AMENDMENT = false
SCIENTIFIC_RESULT_OBSERVED_BEFORE_AMENDMENT = false
```

The parent EXT-B preregistration, protocol, routing, and authority manifest are
unchanged. No model was loaded, no hidden state was accessed, and no
authorization or result exists.

## Recovered rules and change classes

| identity | before | after | source | change class |
|---|---|---|---|---|
| shared family/record IDs | incomplete | exact SHA-256 canonical IDs | EXT-A V3 identity convention, rebound to EXT-B | prospective construction specification |
| family ordering/split assignment | incomplete | exact hash order and 22-family condition blocks | EXT-A V3 enumeration convention, extended to 220 families | prospective construction specification |
| spatial projection | conceptual fields only | exact StepGame row projection and nine-label vocabulary | parent source manifest plus frozen source revision | clarification plus prospective source projection |
| quantitative rule | unbound engineering candidate | signed integers `A=10+i`, `B=5-i`, strict `A>B` | pre-existing script, explicitly re-frozen before data | prospective construction specification |
| WordNet scope | meronymy/holonymy broad | six named meronym/holonym pointer types | parent source policy and WordNet structure | prospective construction specification |
| c01-c10 bytes | conceptual IDs only | exact templates and lexical fields | EXT-A V3 templates, rebound to new IDs | clarification plus prospective byte specification |

The legacy `xa01`–`xa10` identifiers are not emitted. Their conceptual
semantics are used only as pre-existing design evidence; EXT-B emits only the
frozen `c01`–`c10` identifiers.

## Deterministic identity and order

The construction specification defines Unicode normalization, canonical UTF-8
JSON serialization, SHA-256 family and record IDs, and ascending hash ordering.
The first 220 eligible unique families per task are retained. The ordered list
is divided into ten blocks of 22 families. Within each block, positions 0–5
are FIT, 6–13 are DIAGNOSTIC, and 14–21 are EVAL. Family IDs do not contain a
condition; record IDs contain family, condition, and role.

## Task specifications

### Spatial

The frozen StepGame revision and SHA are retained. Only the physical JSONL row
ordinal and relation label are projected; stories, questions, answers,
distractors, reasoning chains, and benchmark text are discarded. The accepted
labels are `above`, `below`, `left`, `lower-left`, `lower-right`, `overlap`,
`right`, `upper-left`, and `upper-right`, interpreted as ARG_A relative to
ARG_B. Argument surfaces are deterministic generated identifiers, never source
story text.

### Quantitative

The pre-existing V3 script is recorded as an unbound engineering candidate,
not silently promoted. This amendment prospectively freezes its deterministic
numeric construction: for one-based within-condition index `i` from 1 through
22, `ARG_A = 10+i` and `ARG_B = 5-i`; values are signed base-10 integers, zero
and negative B values are allowed, equality is excluded, and the relation is
strict `ARG_A > ARG_B`. No outcome-based numeric filtering is allowed.

### Mereological

WordNet 3.0 is bound by the existing archive hash. The allowed pointer types are
`part_meronym`, `member_meronym`, `substance_meronym`, `part_holonym`,
`member_holonym`, and `substance_holonym`. All edges are normalized to
`ARG_A = part/member/substance` and `ARG_B = whole`. Glosses, definitions,
examples, and lexicographer prose are never read into production records.

## Rendering

The separate rendering authority defines exact reference and realization
templates for `c01_lexical_relex` through `c10_anaphoric_reference`, including
allowed fields, punctuation, capitalization, articles, number format, and
whitespace. The renderer is UTF-8, deterministic, and model-independent.

## Validator qualification

`validate_paper_a_ext_b_construction_spec_v1.py` checks the parent hashes,
construction counts, condition identity, source vocabularies, quantitative
formulas, WordNet pointer scope, deterministic identity behavior, and the
absence of legacy condition IDs. Its tests use only synthetic scalar fixtures;
the validator does not generate production records or access models.

## Freeze gates

```text
SPATIAL_CONSTRUCTION_FULLY_BOUND = true
QUANTITATIVE_CONSTRUCTION_FULLY_BOUND = true
MEREOLOGICAL_CONSTRUCTION_FULLY_BOUND = true
C01_C10_RENDERING_FULLY_BOUND = true
DETERMINISTIC_IDENTITY_FULLY_BOUND = true
DETERMINISTIC_ORDERING_FULLY_BOUND = true
```

## Next lifecycle action

`EXT_B_DATASET_CONSTRUCTION_RETRY_UNDER_AMENDMENT_V1`

This amendment does not authorize model execution. The three-of-three data
gate remains required before any model authorization can be considered.

## New artifact hashes

```text
construction_amendment_v1.json = cd147cb513917e411b609915b356e2bbe95c36caf408fbfe408fed4ec655582b
construction_spec_v1.json = a24e254cc7e5d8c65165fe529f5ef5b94463e01825b2db5b6690a31e91f24d1d
rendering_conditions_c01_c10_v1.json = a2d28c586a98c93fe1b1889e8456640713a5143e1e25e870afd847045cf40f67
validate_paper_a_ext_b_construction_spec_v1.py = 21896841a3162176b8a5c233449f9466d23a54a1bbeaf6b1609155dde6158aa2
test_paper_a_ext_b_construction_spec.py = 281bc15d92e50937bbaa0f96f61412f297b5c064f5ce54d79ea9b72ccdab3b9f
```

The construction binding records the final raw SHA-256 of this document and
all five files above. Its own raw SHA-256 is reported externally because a
manifest cannot contain its own fixed-point hash.

## Final flags

```text
EXT_B_PREGEN_AMENDMENT_CREATED = true
EXT_B_PREGEN_AMENDMENT_PROSPECTIVE = true
EXT_B_ORIGINAL_PREREGISTRATION_MODIFIED = false
EXT_B_ORIGINAL_PROTOCOL_MODIFIED = false
EXT_B_OUTCOME_ROUTING_MODIFIED = false
FILES_GENERATED_AS_PRODUCTION_DATA = false
MODEL_INFERENCE_RUN = false
HIDDEN_STATES_ACCESSED = false
MODEL_AUTHORIZATION_CREATED = false
SCIENTIFIC_RESULT_CREATED = false
TEMPORAL_RUNTIME_EXECUTED = false
```
