# EXP-027 Scientific Review and Durable Result Authority

Review type: `INDEPENDENT_POST-HOC_SCIENTIFIC_AUTHORITY_REVIEW`

Archival task: `PA-VALUE-UPLIFT-02-EXP027-DURABLE-ARCHIVAL`

Formal verdict: `SCIENTIFICALLY_VALID_COMPLETE_RESULT_ARCHIVAL_ONLY_MISSING`

Paper A decision: `INCLUDE_AFTER_ARCHIVAL`

## A. Frozen Question and Design

EXP-027 asked whether `Meta-Llama-3.2-1B-Instruct` exhibited the frozen Qwen
profile, the frozen OLMo profile, or a valid third registered profile under the
inherited EXP-026 full source-target fixed-readout compatibility-matrix design.

The frozen design used all 16 Llama decoder blocks as both source and target
depths. Logical block `l` was read from the forward-hook output of
`model.model.layers[l]`; the final block carrier was before the model-level
final RMSNorm. Normalized depth was `l / 15`.

The frozen EXP-024 panel contained 1,760 records from 880 source families,
four semantic classes, ten conditions, and separate FIT, DIAGNOSTIC, and EVAL
partitions. No new split or output-based filtering was permitted.

The registered matrices were:

- `C0(i,j,c)`: balanced accuracy of the source-layer classifier at `i` applied
  directly to EVAL representations from target layer `j` under condition `c`;
- `D(i,j,c) = Cself(i,c) - C0(i,j,c)`;
- `Ccal(i,j,c)`: balanced accuracy after FIT-only `A_mu_sigma` calibration;
- `R(i,j,c) = Ccal(i,j,c) - C0(i,j,c)`.

The frozen preregistration SHA-256 was
`83ba4bb14e87334a6c52a8746f86874eab9578e646abc736057fbd1f4e6322fe`.
The frozen design SHA-256 was
`b37bfd9c3d57bf891ef1993b3a1d7737fcedbe143813d61f5c7ae9ecb0bc5b1a`.

## B. Execution Validity

The completed result was produced at execution commit
`cb581bcfa3640d72f121c34b1cdd59cc3cc672c9`. Its recorded Windows worktree
runner SHA-256 was
`bcbfcf304b356a849ace6158c75c1da86f9c832aeb684b44e0796f3e5f276ca8`.
The corresponding LF-normalized Git blob SHA-256 was
`16f15b7721b3a4e5f6c7883277178d64e2928c91a608c252f9c899b4fe650d97`.
The byte difference is exclusively CRLF-to-LF normalization and is classified
as `BENIGN_METADATA_DIFFERENCE`.

The immutable authority validator and existing result schema/route validator
both passed. Model, protocol, preregistration, dataset, condition panel, data
schema, frozen manifest, and EXP-024 preregistration hashes matched the formal
result binding. Read-only validation of the stored arrays confirmed matrix
shape, orientation, `D`, `R`, condition pooling, SDI, LOW-D selection, and
registered support routing.

## C. Authorization Provenance

The original authorization was
`7df5cc05-2ce7-4a90-ba64-61d575a18885`, SHA-256
`3823b56e92d4d453f17f19212b199968d7b2753ae26db541375a790406a7759c`.
It was consumed once by run attempt `e3493b43352f4453aa044226b8bb1030`.

The recovery authorization was
`b3bba3dd-2d9a-4742-bb0f-27f0f32f131b`, SHA-256
`fdc9e30acde7e3cca2b97c773e8cdb35fea144ec0978971787a2ec117fe74bc4`.
It was consumed once by run attempt `631c80bb448d418e8494fccef8579e30`.
Its consumption-record SHA-256 was
`510f498b9845808dc726c6b483b7a2a9460453af8e90c93bddecee559c4bb08c`.

Each authorization had exactly one matching consumption record. No
unauthorized formal execution or single-use violation was found. The final
result binds the recovery authorization, its consumption record, and the same
run-attempt identity.

## D. Serialization Incident

The original authorized attempt completed extraction and scientific
computation but failed before canonical publication because nested NumPy arrays
were not JSON serializable. No canonical result was created by that attempt.
The console exposed progress stages and the serialization exception but no
matrix values, confidence intervals, support decisions, or registered route.

Failed-attempt outcome exposure is classified as `STRUCTURAL_ONLY`.

## E. Recovery Authority

The serialization repair recursively converted NumPy arrays and scalars only
at the JSON boundary. A second engineering patch made lifecycle matching
authorization-ID-aware so the already consumed original authorization did not
incorrectly consume a distinct recovery authorization.

Source inspection confirmed that these changes did not alter extraction,
model identity, records, conditions, matrix definitions, calibration,
bootstrap, statistics, thresholds, or routing. The recovery authorization was
created before the recovery execution and explicitly bound both engineering
repair identities. Therefore:

- serialization repair science-neutral: `true`;
- post-outcome scientific change: `false`;
- recovery run prospectively authorized: `true`.

## F. Formal Result

Canonical result:
`experiments/exp027/results/exp027_results.json`

SHA-256:
`1f15027d17456f5dc8ff4803452c732af8ba464f70e537195b8833d9d44f6c6d`

Result identity:

- classification: `EXP027_SCIENTIFIC_RESULT`;
- attempt status: `COMPLETED`;
- result status: `VALID_REGISTERED_RESULT`;
- scientific status: `OBSERVED`;
- technical validity: `true`;
- measurement validity: `true`.

Registered primary values:

- distance degradation statistic:
  `0.6077483252598234`;
- distance degradation CI:
  `[0.5949008758383216, 0.6154160155280691]`;
- distance degradation support: `POSITIVE_SUPPORTED`;
- SDI: `-0.41426422986393563`;
- SDI CI: `[-0.4342173411679606, -0.39239628027572504]`;
- SDI classification: `TARGET_DOMINANT`;
- LOW-D recovery: `0.0014030612453970375`;
- LOW-D effective n: `49`;
- LOW-D positive fraction: `0.32653061224489793`;
- LOW-D CI: `[0.0007325690004461426, 0.002186791592619705]`;
- LOW-D support: `SUPPORTED`;
- D localization: `0.15216393981464418`, boundary `[2]`;
- R localization: `0.15013367153058252`, boundary `[1]`;
- overall registered classification: `THIRD_REGISTERED_PROFILE`.

## G. Registered Interpretation

Under the registered measures, degradation increases with normalized
source-target distance. Target-depth variation dominates source-depth
variation under the registered SDI, and LOW-D recovery is positively
supported. The three-component profile matches neither frozen reference
profile exactly, so the preregistered route is `THIRD_REGISTERED_PROFILE`.

EXP-027 is scientifically comparable to EXP-026. Matrix definitions,
calibration, panel, split semantics, orientation, statistical procedure, and
LOW-D procedure are identical. The block count, normalization denominator, and
module hook are registered model-specific adaptations preserving the same
scientific carrier semantics.

## H. Limitations

The result does not establish architecture or model-family causality. It does
not prove manifold structure, semantic equivalence, information transport,
invariance, functional binding, behavioral control, or a universal law across
models. Supported LOW-D recovery is a registered measurement result, not a
mechanistic explanation.

## I. Paper A Admissibility

EXP-027 is an authentic, completed, authorized registered scientific result.
Its prior deficiency was durable archival rather than scientific validity.
With the immutable result and complete authorization lineage tracked and bound
by the canonical manifest, its Paper A disposition is:

`PAPER_A_EXP027_DECISION = INCLUDE_AFTER_ARCHIVAL`

The result must be reported within the interpretation and claim boundaries
above.
