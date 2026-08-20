# EXP-026 Task 101D-R3 Repair Audit

Status: `READY_FOR_FINAL_TARGETED_R3_REREVIEW`

This repair is limited to the five validation gaps reported by Task 101D-R2-RR.
It does not change frozen authorities, models, layer sets, thresholds, statistics,
routing precedence, or scientific data.

## Closed findings

1. **Cross-object schema:** serialized matrices now bind source/target roles,
   layer identities, and per-axis slice digests. Validation recomputes those
   bindings and the frozen D, R, Dbar, Rbar, diagonal, eligibility, coverage,
   profile-status, and routing relations.
2. **Production Ccal golden:** a hand-specified calibration fixture calls
   `_compute_c_cal_for_partition` directly. Its expected matrix is specified
   independently from raw vectors, fixed means/scales, and classifier outputs.
   R is checked separately against an independent C0 anchor.
3. **Carrier identity:** model loading binds the exact canonical decoder-block
   objects and expected architecture classes. Every extraction rejects later
   reorder, replacement, duplication, embedding, or final-normalization
   substitution.
4. **Normalized depth:** direct L=4 coordinate and pair-distance goldens test
   `l/(L-1)` independently from the Spearman statistic.
5. **NOT_EVALUABLE serialization:** `confirmatory_status` is serialized and a
   forced coverage-failure profile completes profile-to-result validation.

## Test evidence

| Gate | Production function under test | Independent expectation/invariant | Executable cases |
| --- | --- | --- | ---: |
| Cross-object schema | `validate_result_schema` | stale axis binding and frozen algebra/status/routing relations must reject | 9 |
| Production Ccal | `_compute_c_cal_for_partition` | hand-computed 2x2x10 Ccal plus independent R integration | 2 |
| Carrier identity/order | `bind_logical_block_carriers`, `logical_block_carriers` | exact bound object sequence and frozen model/block classes | 8 |
| Normalized depth | `normalized_depth`, `normalized_pair_distance` | `[0, 1/3, 2/3, 1]` and three fixed pair distances | 3 |
| NOT_EVALUABLE serialization | `_serialize_profile`, `validate_result_schema` | coverage-failure roundtrip plus missing/contradictory status rejection | 2 |

Targeted sabotage covers coherent matrix transpose, zero production Ccal,
reversed carriers, raw-index depth coordinates, and removed
`confirmatory_status`.

## Preserved paths

- B1 shared formal/synthetic executor
- B2 authorization-before-consumption binding
- B3 coverage failure routes to NOT_EVALUABLE
- B4 source-family cluster bootstrap
- M3 synthetic formal end-to-end qualification
- exclusive result publication and race rejection

The science firewall remained closed: no real EXP-026 FIT, DIAGNOSTIC, or EVAL
records were accessed; no formal authorization or scientific result was created.

## Qualification identities

- Repair commit: `deaa9468b96810d701f6f52d429af7215aa76b36`
- Runner SHA-256: `fe588621c2e4699e068180cc7787101a24a8337c0a94c6cd25db42bb466b9605`
- Focused tests: `85 passed` (`44` scikit-learn deprecation warnings)
- Engineering qualification SHA-256:
  `4849c65e7f04257c05fc5dd04f710a8bdf62a48ab27ef3eab6480ffd317a4725`
- Formal-pipeline qualification SHA-256:
  `ea44190d0824bdacca73de58af44a700712a8a30d1f6aab6ea3b8ef92ac62da8`
- Superseded formal qualification:
  `1665c116a48d7d000bd833caa19c574dd62804238fb1384b154405e483caa495`
