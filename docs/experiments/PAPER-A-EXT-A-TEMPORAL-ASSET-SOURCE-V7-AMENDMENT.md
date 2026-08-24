# PAPER-A EXT-A Temporal Asset Source V7 Amendment

Status: `FROZEN`

This is a prospective access-backend amendment only. It does not perform
formal temporal acquisition, create temporal pairs, create a real asset bank,
create a panel, or run model inference.

## Scope

V7 permits the future temporal source to be queried through QLever:

- endpoint: `https://qlever.dev/api/wikidata`
- raw graph scope: `UNIFIED`
- source: Wikidata
- initial formal offset: `0`

The V6 authority remains byte-for-byte unchanged. The historical V6 offset-0
page is evidence of the prior WDQS lineage only and is not consumed by V7.
V7 must not resume from the V6 checkpoint at offset 100 and must not mix V6
and V7 pages.

## Frozen Main-View Reconstruction

Before `ORDER BY`, `LIMIT`, or `OFFSET`, V7 applies the published WDQS
scholarly exclusion rule. An entity is excluded from the reconstructed main
view if it has either:

1. a non-deprecated `P13046` statement; or
2. a direct non-deprecated `P31` value in the frozen scholarly class list.

`P279` ancestry is not used for graph splitting. The exact serialized rule is
in `experiments/paper_a_ext_a/v7_main_view_rule.json`. The query-construction
implementation is in `experiments/paper_a_ext_a/qlever_v7_main_view.py`.

The amendment reconstructs the published membership rule over QLever's
unified graph. It does not claim that QLever and legacy WDQS are globally
identical or that their live snapshots are byte-identical.

## Scientific Contract Preserved

The following remain unchanged from V6:

- Wikidata and `P585` as the source/property;
- direct `P31` or `P31/P279` ancestry to `Q1190554` for event eligibility;
- exactly one canonical P585 value;
- proleptic Gregorian `Q1985727`;
- precision at least 11;
- surface-date leakage filtering;
- ascending date then QID ordering;
- consecutive unequal-date pairing;
- target of 220 temporal source families;
- deterministic V3 rendering and all task/semantic authorities.

## Qualification Boundary

QEQ-R2 established QLever query compatibility and fixed-field concordance,
and observed raw-unified global-order risk from scholarly-only literal-P585
entities. The bounded evidence did not establish global candidate equivalence.
Therefore no formal V7 acquisition is authorized by this amendment alone.

## Validation and Next Action

The V7 validator rejects raw-unified acquisition, V6/V7 page mixing, a
nonzero initial offset, filter placement after pagination, hash drift, and
pre-existing formal outputs. The next permitted step is:

`PA-EXT-A-005R2-RESUME-FORMAL-TEMPORAL-ACQUISITION-UNDER-V7`

That step is separate from this freeze and must begin at V7 offset 0.
