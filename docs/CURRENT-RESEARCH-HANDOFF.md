# Current Research Handoff

This file is a navigation and status snapshot, not an independent source of
scientific truth. Canonical artifacts, frozen manifests/hashes, result files,
validators, and Git commits outrank this document. Preserve and report
conflicts rather than silently reconciling them.

Repository base at time of writing: `347ce1a3a92790743a05a7ab7417f4cd503e31d3`
(`main`). Pre-existing untracked local EXP-020A/EXP-021/EXP-023/EXP-024/EXP-025/EXP-026
evidence remains local and must not be added, rewritten, or deleted by this
handoff.

## 1. Current Research Question

The central question is conservative: how do task-relevant hidden
representations move, degrade, recalibrate, and potentially need transport
across layers and interventions, and what minimum evidence is required before
claiming geometry, causal role, invariant preservation, functional binding, or
behavioral control?

The current empirical focus is a model/depth compatibility profile. After Qwen
and OLMo showed materially different fixed-readout source/target organization,
the active scientific route is independent third-model triangulation, not a
new mechanism theory.

Current chain:

```text
representation
-> local manipulability
-> fixed-readout depth compatibility
-> cross-model organization
-> third-model triangulation
-> minimum sufficient alignment (future)
-> invariant / functional binding (future)
```

Paper A remains a bounded, derived-evidence manuscript. It is not a source of
new scientific authority, and this handoff does not revise its claims.

## 2. Evidence Chain: EXP-017 -> EXP-027

Each item records the scientific status, not only the engineering state.

| Experiment | Scientific status | Bounded reading |
| --- | --- | --- |
| EXP-017 | `NOT_SUPPORTED` | Local manipulability did not produce task-specific behavioral control. |
| EXP-018 | `SUPPORTED` | Held-out, fit/eval-separated target-directed local representation movement on its fixed controlled design. |
| EXP-019 | `FAILED` | Independent output-only evaluator failed generalization; behavioral targetness remains unresolved. |
| EXP-020A | `SUPPORTED` | Same-family larger-model replication of the EXP-018 representation effect. |
| EXP-021 | `FAILED` | Fixed source-semantic cross-layer readout qualification failed at the frozen clean-checkpoint gate. |
| EXP-022A | `PARTIALLY_SUPPORTED / SPLIT_DEPENDENT` | `D_fixed` partial concordance, supported in Split B but not Split A; A1 featurewise recalibration is descriptive; A2 same-family refit rescue is not supported. |
| EXP-023 | `NO_REPLICATION` | Independent preregistered no-replication result: Split A calibration rescue `+0.25` supported, Split B `0.0` unsupported; mean-vs-scale decomposition is descriptive only. |
| EXP-024 | `NOT_SUPPORTED_BY_EXP024_PRIMARY_TEST` | Simple independent degradation-magnitude susceptibility predictor failed; `S_diag > 0` and `G_eval > 0` in 10/10 conditions are descriptive panel observations. |
| EXP-025 | `POST_HOC_PROTOCOL_RECOVERY`, `D-_G+` | OLMo cross-model panel: degradation breadth `NOT_ESTABLISHED`; FIT-only recalibration recovery `LIMITED_SUPPORT`. |
| EXP-026 | `P3_MATERIALLY_DIFFERENT_MODEL_SIGNATURES` | Valid registered result showing model-dependent compatibility organization. |
| EXP-027 | `ENGINEERING_PREPARATION_ONLY` | Third-model authority/runtime/provenance qualified; no scientific design freeze, authorization, formal run, or outcome yet. |

## 3. EXP-026 Registered Result and P3 Routing

EXP-026 is complete and must not be rerun, edited, or reinterpreted after the
fact.

- Canonical result: `experiments/exp026/results/exp026_results.json`
- Canonical result SHA-256:
  `9a5bed41b432e2f89b0873869d76e1f5775f9b38caff9472553fca335bbba551`
- Authorization ID: `b3763f43-d365-4a24-86fc-263f53dc84cb`
- Authorization SHA-256:
  `83adcafa0648e94d8a50b7132bc9713abf2d9ee58bb930690b775ec93248dcd2`
- Consumption SHA-256:
  `4a35bfed3622ef82540e6bd42a843a56c9b5c465a686c1e2201ea5de012cd82a`
- Runner SHA-256:
  `6ab29c35889ce35b9d4bc9ee98d2665865a088312940f10815714a574d2060a0`
- Registered route: `P3`

Registered model signatures:

- Qwen: distance association `0.7049462571528698`, `POSITIVE_SUPPORTED`; SDI
  `-0.17355352410373298`, `TARGET_DOMINANT`; LOW-D recalibration recovery
  `NOT_SUPPORTED`.
- OLMo: distance association `0.7519250367843754`, `POSITIVE_SUPPORTED`; SDI
  `0.5249651786448143`, `SOURCE_DOMINANT`; LOW-D recalibration recovery
  `SUPPORTED`.

Claim ceiling:

- Depth-distance-associated fixed-readout compatibility structure is supported
  in both tested models only.
- Materially different cross-model source/target organization is supported.
- This does not establish architecture/family causality, transport, invariant
  preservation, functional binding, or behavior.
- Do not claim a uniform mechanism across models.

## 4. EXP-027 Current State

- Engineering status: `EXP027_102A_LQ_COMPLETE = true`.
- Selected model: `Meta-Llama-3.2-1B-Instruct`.
- Model source: `META_OFFICIAL_NATIVE_DISTRIBUTION`.
- Scientific design: `NOT_YET_PREREGISTERED`.
- Formal authorization: `false`.
- Formal run: `false`.
- Scientific outcome: `NOT_OBSERVED`.
- Real FIT/DIAG/EVAL access: `false`.

Next task is exactly:

```text
102B_EXP027_PREREGISTRATION_AND_FROZEN_DESIGN
```

Do not freeze an EXP-027 protocol, create an authorization, run the model on
formal scientific data, or compute SDI / LOW-D recovery / third-model
classification in the current stop state.

## 5. Llama 3.2 Native -> HF Conversion Provenance

- Native source:
  `D:\AI_Cache\llama_home\.llama\checkpoints\Llama3.2-1B-Instruct`
- Converted source:
  `D:\AI_Cache\llama_hf\Llama3.2-1B-Instruct-meta-converted-v4463-attempt3`
- Native files have been MD5-verified against the Meta checklist and SHA-256
  captured.

Native SHA-256:

- `checklist.chk`:
  `EFEFC79FC47ECCE1C3E06A6AE77A4CDDC7E6078F822EFBA22E4FC7F9DA02400E`
- `consolidated.00.pth`:
  `FC17D497DF5E4175B3A8ACB4F5865B26F7FC1B009B25BEF814B95FDE10E8A1F3`
- `params.json`:
  `1D616A44F3CDAC29B9288CF14718B76EB1BED56ED38BE1F7E39B06ED139E3733`
- `tokenizer.model`:
  `82E9D31979E92AB929CD544440F129D9ECD797B69E327F80F17E1C50D5551B55`

Conversion history:

- Attempt 1: `FAILED_TOKENIZER_VOCAB_MISMATCH`; not reused.
- Attempt 2: `FAILED_MISSING_ACCELERATE_DEPENDENCY`; not reused.
- Attempt 3: `PASS`.

Converted checkpoint:

- `model.safetensors` SHA-256:
  `1FF795FF6A07E6A68085D206FB84417DA2F083F68391C2843CD2B8AC6DF8538F`
- Native tensors: `147`.
- Converted tensors: `146`.
- `output.weight` is tied to `tok_embeddings.weight`; no separate
  `lm_head.weight` is stored.
- All direct-mapped tensors match exactly.
- Q/K tensors require the official Meta-to-HF permutation; reconstructed Q/K
  tensors match exactly with `max_abs_diff = 0.0`.
- Provenance status: `PASS`.
- Model authority qualification: `true`.

Converted runtime identity:

- Architecture: `LlamaForCausalLM`
- Model type: `llama`
- Hidden size: `2048`
- Intermediate size: `8192`
- Layers: `16`
- Attention heads: `32`
- KV heads: `8`
- Vocab size: `128256`
- Max position embeddings: `131072`
- Rope theta: `500000.0`
- Tied word embeddings: `true`
- Runtime dtype: `torch.bfloat16`
- GPU: `NVIDIA GeForce RTX 5060 Laptop GPU`
- Tokenizer vocab: `128256`; BOS `128000`, EOS `128001`, EOT `128009`
- Chat template used: `false`
- Input mode candidate: `RAW_TEXT`; this is not frozen until Task 102B.

## 6. Carrier Hook Final-Layer Final-Norm Trap

The final model hidden state is not interchangeable with the final decoder
block forward-hook output.

- `model(...).hidden_states[-1]` is the post-model-final-normalization hidden
  state.
- The final decoder-block forward-hook output is pre-final-normalization for
  the final block.
- The production carrier API is
  `FORWARD_HOOK_DECODER_BLOCK_OUTPUT`.
- Logical layer `l` maps to `model.model.layers[l]`.
- Extraction path: hook output -> last valid token -> detach -> CPU ->
  `float32` -> NumPy.
- `EXP027_FINAL_HIDDEN_STATE_SEMANTICS = POST_FINAL_NORM_CONFIRMED`.
- `EXP027_CARRIER_MAPPING = VERIFIED`.

This prevents accidentally aliasing `block27_pre_final_rmsnorm` to
`block27_post_final_rmsnorm` in Qwen-style systems and preserves the correct
pre-final-normalization checkpoint semantics for EXP-027.

## 7. Runtime Engineering: Bootstrap and Outcome-Blind Progress

### Bootstrap 7.6059x equivalence

- The EXP-026 reference implementation is preserved and not rewritten.
- The optimized prototype is
  `experiments/exp027/engineering/exp027_bootstrap_optimized_prototype.py`.
- Focused test result: `9 passed`.
- Equivalence checks: draw sequence, registered statistic, support
  classification, and routing all `PASS`.
- Synthetic benchmark speedup: `7.6059x`.
- Optimization precomputes exact classwise sufficient counts so each bootstrap
  replicate aggregates counts instead of repeatedly fitting/scoring on raw
  observations.

### Outcome-blind progress

- Helper:
  `experiments/exp027/engineering/exp027_progress.py`
- Focused test result: `4 passed`.
- Allowed output: timestamp, stage, completed, total, percentage, elapsed,
  optional ETA, heartbeat, publication status.
- Forbidden before canonical publication: rho, SDI, LOW-D recovery, CI,
  support, route, condition-specific scientific values, and model-comparison
  outcomes.
- Optional state file uses atomic replacement and contains only
  execution-progress fields.
- Console output is plain stdout and compatible with PowerShell `Tee-Object`.
- `EXP027_OUTCOME_BLIND_PROGRESS = IMPLEMENTED`.
- `EXP027_PROGRESS_CONTAINS_SCIENTIFIC_VALUES = false`.

## 8. Theory Assets: Supported vs Candidate vs Inspiration

### Empirically supported claims

- EXP-018/EXP-020A: local target-directed representational movement and
  same-family larger-model replication.
- EXP-026: depth-distance-associated fixed-readout compatibility structure in
  both tested models, and materially different cross-model organization.
- EXP-026: Qwen target-dominant vs OLMo source-dominant registered
  classification.

### Prospective candidates, not validated

- `Minimum Sufficient Alignment Operator`:
  `PROVISIONAL_RESEARCH_CONCEPT`, name not frozen. Placeholder is
  `k* = min { k : Delta_EVAL(T_k) >= tau }`, with `tau` unregistered.
- `Residual-Flow Hypothesis`:
  `PROSPECTIVE` / `NOT_YET_VALIDATED`. It is motivated by residual
  architectures and the EXP-026 profile, but is not confirmed by ResNet,
  EXP-026, or EXP-027. It is not a new EXP-027 confirmatory endpoint.
- `KAN / Constrained Operator-Family Inspiration`:
  `ACTIVE_INSPIRATION_ASSET` / `NOT_EMPIRICALLY_VALIDATED_BY_PROJECT`.
  Provides a future operator ladder `T0` identity through `T5` general
  constrained nonlinear operator.
- `Invariant Preservation`: `DEPENDENT_FUTURE`; no specific invariant is
  validated.
- `Representation Trajectory Conserved Structure`: prospective
  `I(h_{l+1}) ~ I(h_l)` or `dI(h(t))/dt ~ 0`; no specific invariant is frozen.

### Analogy / inspiration only

- Kakeya-style direction/overlap inspiration: `ANALOGY_ONLY`; not a
  latent-space theorem.
- Ten-point unit-disk covering question: `INCUBATING`; motivates the
  overlap-is-not-destructive-interference question, but is not direct neural
  capacity evidence.
- KAN/KART is architectural and operator-family inspiration; it does not
  validate cognitive folding, coordinate transport, invariant reasoning, or
  functional binding.
- Functional binding: `DEPENDENT_FUTURE`; not supported by any current
  canonical experiment.

### Frozen statuses KAN must not alter

- `HYP_CALIBRATION_CONDITIONAL_002 = NOT_SUPPORTED`
- `GENERAL_CALIBRATION_REPLICATION = NOT_ESTABLISHED`
- `GENERAL_COORDINATE_TRANSPORT = NOT_TESTED`
- `FUNCTIONAL_BINDING = NOT_TESTED`
- `BEHAVIORAL_CONTROL = NOT_ESTABLISHED`
- `HYP-TRANSPORT-001` remains unchanged.

## 9. Prohibitions and Boundary Rules

Do not:

- perform post-hoc rescue or reinterpret a frozen negative result;
- rerun, rewrite, or delete any frozen/canonical EXP-017 through EXP-026 result,
  protocol, authorization, or consumption evidence;
- create an EXP-027 authorization or formal run in the current stop state;
- access EXP-027 formal FIT/DIAG/EVAL data before the 102B preregistration and
  authorization sequence;
- modify the frozen EXP-027 protocol/dataset/model authority;
- add Residual-Flow or KAN as an EXP-027 confirmatory endpoint;
- modify Paper A claims in this research-asset handoff;
- use `git add .` / `git add -A`.

Conceptual boundaries:

- decodability is not causal role;
- local manipulability is not behavioral control;
- probe recovery is not functional binding;
- alignment/recalibration recovery is not functional binding;
- invariant preservation is not functional binding;
- fixed readout failure is not information disappearance;
- one successful model pair is not a scaling law;
- a material model-dependent difference is not architecture/family causality;
- EXP-026 is motivation for operator-dynamics study, not confirmation of
  Residual-Flow.

## 10. Canonical Source Pointers

- Research spine: `docs/research/RESEARCH-SPINE.md`
- Experiment lineage: `docs/research/EXPERIMENT-LINEAGE.md`
- Claim ledger: `docs/research/CLAIM-LEDGER.md`
- Hypothesis ledger: `docs/research/HYPOTHESIS-LEDGER.md`
- Construct registry: `docs/research/CONSTRUCT-REGISTRY.md`
- Research asset map: `docs/research/RESEARCH-ASSET-MAP.md`
- Current brief: `docs/research/CURRENT-RESEARCH-BRIEF.md`
- EXP-027 authority:
  `experiments/exp027/engineering/EXP-027-LLAMA-MODEL-AUTHORITY.md`
- EXP-027 provenance:
  `experiments/exp027/engineering/llama32_native_converted_provenance.json`
- EXP-027 model authority qualification:
  `experiments/exp027/engineering/llama32_model_authority_qualification.json`

## 11. Immediate Next Gate

- `EXP-027` status: `102A_LQ COMPLETE`.
- Next: `102B_EXP027_PREREGISTRATION_AND_FROZEN_DESIGN`.
- No EXP-027 scientific computation, authorization, formal run, or result is
  authorized here.
- Do not route to operator-capacity diagnosis or Residual-Flow validation before
  the third-model triangulation evidence is available and the preregistered
  decision tree selects it.
