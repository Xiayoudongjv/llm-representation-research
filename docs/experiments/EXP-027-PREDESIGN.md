# EXP-027 Pre-Design Note

Status: `PRE_DESIGN_ONLY`

Experiment status: `EXP027_FORMAL_DESIGN_FROZEN = false`

This is a prospective research-routing note. It is not a frozen preregistration,
not an authorization, and not a scientific result.

## Purpose

`EXP027_PRIMARY_PURPOSE = THIRD_MODEL_TRIANGULATION`

The next experiment must answer whether an independent third model exhibits:

- A. a Qwen-like target-dominant organization;
- B. an OLMo-like source-dominant organization; or
- C. neither / a third structural regime.

This is triangulation, not rescue. The question is not whether another
significant result can be obtained.

## Frozen Reference Signatures

EXP-027 must not rerun Qwen or OLMo.

`EXP027_QWEN_OLMO_RERUN_REQUIRED = false`

Frozen EXP-026 references:

- Qwen signature: `TARGET_DOMINANT`, distance `POSITIVE_SUPPORTED`, LOW-D `NOT_SUPPORTED`.
- OLMo signature: `SOURCE_DOMINANT`, distance `POSITIVE_SUPPORTED`, LOW-D `SUPPORTED`.
- Canonical result: `experiments/exp026/results/exp026_results.json`
- Canonical result SHA-256: `9a5bed41b432e2f89b0873869d76e1f5775f9b38caff9472553fca335bbba551`

## Third-Model Selection Criteria

Prefer a model with:

- roughly comparable parameter scale;
- independent model family/training lineage;
- full hidden-state accessibility;
- decoder-block carriers that can be frozen cleanly;
- BF16/local execution feasibility on the current 8GB GPU;
- no quantization if avoidable;
- no offload-induced measurement change if avoidable.

Do not select a model because its preliminary outcome appears favorable.

## Candidate to Review

Primary candidate for Task 102A review: `Llama-3.2-1B-Instruct`.

`EXP027_LLAMA_1B_CANDIDATE_REVIEW_REQUIRED = true`

Before any freeze, verify:

- exact model ID and revision;
- architecture and model class;
- hidden size;
- number of decoder blocks;
- tokenizer/chat-template semantics;
- BF16 memory feasibility;
- licensing/access;
- neutral carrier extraction;
- comparable raw-text input semantics.

Explicitly reject `Llama-3-8B-Instruct` as the primary triangulation model if it
introduces avoidable scale plus quantization/offload confounding.

## EXP-027 Design Principle

- Single-new-model triangulation.
- Reuse frozen conceptual dataset/panel semantics where valid.
- Independently compute the same registered structural signature for the third model.
- Do not use EXP-026 Qwen/OLMo outputs as new confirmatory rescues.

## Prospective Comparison

Define, before third-model outcomes, how the third-model signature will be
compared to the two frozen reference profiles. Prefer low-dimensional
registered signature components:

- distance association class;
- SDI class;
- LOW-D recovery class;
- localization status if frozen/evaluable.

Do not compare arbitrary heatmap appearance as confirmatory evidence.

## Prospective Routing After EXP-027

- Third model Qwen-like -> investigate a target-organized compatibility regime.
- Third model OLMo-like -> strengthen the source/readout-interface mechanism route and prioritize minimum sufficient alignment operator.
- Third model distinct from both -> prioritize a model-dependent compatibility taxonomy/reference organization before universal operator claims.

Exact thresholds and routing must be preregistered later. This note does not
freeze them.

## Governance

- `EXP027_FORMAL_DESIGN_FROZEN = false`
- `EXP027_FORMAL_RUN_AUTHORIZED = false`
- `EXP027_REAL_DATA_ACCESSED = false`
- No EXP-027 canonical result may be created.
- Next task: `102A_EXP027_THIRD_MODEL_SELECTION_AND_DESIGN_AUDIT`