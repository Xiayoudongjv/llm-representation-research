# PAPER-A CKA RUN AUTHORITY V1

Status: `PRE-RUN_BOUNDARY_FROZEN`

This document defines the execution boundary for the Paper A secondary CKA
analysis. It is not a scientific result and does not authorize inference by
itself.

## Frozen scope

- Split: `EVAL` only.
- Models: exactly Qwen, OLMo, and Llama, using the identities frozen in the
  CKA protocol.
- Carrier: decoder-block post-block residual at the registered
  `model.model.layers[layer]` hook location.
- Method: centered linear CKA with float64 accumulation.
- No PCA, random projection, training, probe fitting, or learned alignment.
- Sample order and `sample_order_hash` remain those of the frozen EVAL panel.

## Boundary conditions

Before execution, the validator must confirm that the Paper A canonical
science files have their frozen hashes and that no CKA asset, matrix, or
comparison result exists. The execution boundary must fail closed if either
condition is violated.

This authority does not permit modification of Paper A canonical results,
claim registers, figures, tables, or other scientific authorities. It also does
not permit model execution in the validation step.

## Intended outputs after a separately approved run

Only after the pre-run boundary is independently satisfied may the explicit
CKA tools create model-specific hidden-state assets, CKA matrices, and
comparison tables under an external run-output directory. Those outputs are
not present under this authority freeze.

## Scientific claim ceiling

If later executed and validated, CKA may provide a secondary descriptive
comparison between centered representation similarity and the immutable
operational C0/D/R measurements. It cannot establish semantic equivalence,
geometric equivalence, causal mechanism, information flow, behavioral control,
or cross-task universality.

Required pre-run state:

```text
CKA_RUN_AUTHORITY = FROZEN
CKA_INFERENCE_PERFORMED = false
CKA_RESULTS_CREATED = false
PAPER_A_CANONICAL_FILES_MODIFIED = false
```

