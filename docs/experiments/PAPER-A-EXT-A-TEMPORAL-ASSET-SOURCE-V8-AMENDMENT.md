# PA-EXT-A V8 Literal-Date Candidate Binding Amendment

V7 formal QLever acquisition was stopped before scientific output because
QLever returned Wikibase `genid` objects for the frozen direct `wdt:P585`
candidate binding. The downstream frozen temporal contract requires a usable
literal date plus calendar and precision metadata, so those candidates were
deterministically ineligible.

The preserved V7 blocker record is: 10 candidate pages verified, next offset
1000, 0 eligible events, 0 temporal families, no canonical temporal output,
and no model inference. The V7 raw lineage is not consumed by V8.

V8 makes one response-schema correction only:

```sparql
FILTER(ISLITERAL(?date))
```

The filter remains after the frozen official WDQS main-view reconstruction and
before ordering and pagination. P585, Gregorian calendar `Q1985727`, precision
at least 11, occurrence ancestry through `P31`/`P279` local BFS, leakage rules,
ordering, pairing, and the target of 220 temporal families are unchanged.

V7 remains historical and is not consumed by V8. V8 starts at offset 0 with a
separate lineage. This amendment contains only bounded qualification; no V8
formal acquisition, temporal families, panel, or model inference is performed
here.
