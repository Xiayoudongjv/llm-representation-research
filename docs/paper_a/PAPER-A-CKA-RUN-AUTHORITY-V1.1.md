# PAPER-A CKA RUN AUTHORITY V1.1

Status: `PRE-RUN_BOUNDARY_FROZEN`

This V1.1 document is the data-contract correction to
`PAPER-A-CKA-RUN-AUTHORITY-V1`. It changes only the frozen EVAL sample count.
It does not authorize inference by itself and does not alter Paper A science.

## Corrected data contract

- Split: `EVAL` only.
- EVAL sample count: **640 unique records**.
- Sample order: the frozen dataset-file order filtered to EVAL.
- No sampling or selection was performed.

The previous count of 320 came from an incomplete asset inventory. Inspection
of the frozen protocol dataset identified 640 unique EVAL IDs. The correction
does not redraw, filter, or otherwise select samples.

## Preserved execution scope

- Models: exactly Qwen, OLMo, and Llama, using the identities frozen in the
  CKA protocol.
- Carrier: decoder-block post-block residual at the registered
  `model.model.layers[layer]` hook location.
- Method: centered linear CKA with float64 accumulation.
- No PCA, random projection, training, probe fitting, or learned alignment.
- Paper A canonical results, claim register, comparison targets, and claims
  are unchanged.

## Boundary conditions

Before execution, the validator must confirm that the Paper A canonical
science files have their frozen hashes and that no CKA asset, matrix, or
comparison result exists. The execution boundary must fail closed if either
condition is violated.

This authority does not permit modification of Paper A canonical results,
claim registers, figures, tables, or other scientific authorities. It also does
not permit model execution in the validation step.

Required pre-run state:

```text
CKA_RUN_AUTHORITY = FROZEN_V1.1
CKA_EVAL_SAMPLE_COUNT = 640
CKA_INFERENCE_PERFORMED = false
CKA_RESULTS_CREATED = false
PAPER_A_CANONICAL_FILES_MODIFIED = false
```

