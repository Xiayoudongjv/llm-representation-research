# EXP-026 101D-R2 Targeted Repair Record

## Scope

This record addresses only the remaining major qualification findings from
101D-RR: deep result-schema validation (M1), independent numeric goldens
(M2), and adversarial semantic test power (M4). It does not change any frozen
scientific authority, model identity, layer set, threshold, routing rule, or
scientific panel.

## Repaired qualification surface

- Result schema 1.1.0 validates exact model identities, provenance,
  authorization and consumption identities, execution status, technical
  validity, routing metadata, matrix metadata, and matrix algebra.
- Serialized `D`, `R`, `Dbar`, and `Rbar` must agree with their registered
  `C0` and `Ccal` inputs; stale metadata paired with transposed values fails.
- The synthetic qualification uses a ten-condition asymmetric independent
  golden fixture for `D`, `R`, pooled matrices, distance association, SDI,
  low-D recovery, and routing.
- Focused tests include nested-schema rejection cases, semantic sabotage
  cases, carrier identity checks, asymmetric production `C0`, noncanonical
  probability columns, frozen low-D pair membership, and publication races.

## Qualification boundary

The former synthetic formal-pipeline qualification
`8628426f28a9d13fed3c20ba16ed01e4cceb9c4a5b548ad4afebf4dc8c78ff93` is
retained as historical evidence only. The versioned R2 qualification artifact
supersedes it because 101D-RR identified remaining major qualification gaps.

The R2 artifact must bind the committed runner identity, the six frozen
authority hashes, the new engineering qualification identity, and the focused
test-module hash. Qualification may establish only
`READY_FOR_INDEPENDENT_REREVIEW`; it neither creates a formal authorization nor
permits a formal EXP-026 execution.

## Science firewall

No real EXP-026 FIT, DIAGNOSTIC, or EVAL record is accessed by this repair or
by its synthetic qualification. No authorization, consumption record, or
scientific result is created.
