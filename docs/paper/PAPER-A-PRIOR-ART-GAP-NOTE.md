# Paper-A Prior-Art Gap Note

Status: `NON-AUTHORITATIVE_DERIVED_ASSET`

This document records a targeted prior-art positioning review for Paper-A. It
is not a frozen scientific authority and must not outrank canonical experiment
results, the claim ledger, or the hypothesis ledger.

## Known Prior Art

### Tuned Lens

- Reference: Belrose, Furman, Smith, Halawi, Ostrovsky, McKinney, Biderman,
  and Steinhardt, "Eliciting Latent Predictions from Transformers with the
  Tuned Lens", arXiv:2303.08112.
- Core method: trains a per-block affine probe/lens from hidden states to
  vocabulary/logit space, then uses those tuned probes to inspect iterative
  latent predictions across depth.

### Model Stitching

- Reference: Bansal, Nakkiran, and Barak, "Revisiting Model Stitching to
  Compare Neural Representations", NeurIPS 2021, arXiv:2106.07682.
- Core method: connects the bottom of one trained model to the top of another
  through a simple trainable layer and uses the stitched model's performance
  as functional evidence about representational compatibility.

### Functional-Alignment Caution

- Reference: Smith, Mannering, and Marcu, "Functional Alignment Can Mislead:
  Examining Model Stitching", ICML 2025 Spotlight.
- Core finding: models can be functionally aligned while representing very
  different information. Functional/stitching performance therefore does not
  by itself establish informational or representational similarity.

## What It Already Establishes

Tuned Lens establishes:

- hidden representations often require layer-specific affine readouts;
- iterative/linear decoding can expose nontrivial depth-wise prediction
  dynamics;
- layerwise probe families are a useful engineering/lens tool.

Model stitching establishes:

- simple trainable layers between bottom and top model components can restore
  substantial task performance;
- stitching performance is a functional compatibility signal under carefully
  bounded interpretation.

Functional-alignment caution establishes:

- functional recovery can occur even when the underlying representations are
  not informationally similar;
- "does a simple adapter recover performance?" is not equivalent to "are the
  representations meaningfully aligned?"

## What Paper A Must Not Claim as Novel

Paper-A must not claim novelty merely because:

- hidden representations require layer-specific readouts;
- affine maps can align or decode representations across layers;
- a trained linear/affine transformation restores task performance;
- iterative/linear probes reveal depth-wise prediction structure.

The bounded Paper-A contribution is not "affine readouts exist" or "layerwise
readout mismatch exists." Those phenomena are already known in the cited
literature.

## Our Distinct Experimental Question

Paper-A's working distinction:

- A fixed semantic-class readout is held constant across depth.
- Only low-capacity FIT-only featurewise recalibration is allowed.
- No layer-specific classifier refitting is used for the primary mechanism.
- Independent replication revealed heterogeneous rather than uniform rescue.
- EXP-024 has now tested whether that susceptibility can be predicted
  independently before confirmatory EVAL outcomes are observed.

Prospective EXP-024 question:

> Can a condition-level diagnostic measured on independent DIAGNOSTIC source
> families identify conditions where the fixed block16 reference readout
> becomes incompatible at block27-pre, and does that diagnostic predict
> FIT-only featurewise recalibration benefit on source-family-independent EVAL
> families?

## EXP-024 Outcome

EXP-024 completed with a valid canonical result:

- Primary `rho = 0.28401877872187725`.
- Exact one-sided permutation `p = 0.2115079365079365`.
- Registered support rule `rho > 0 AND p <= 0.05`: not satisfied.
- `S_diag > 0` and `G_eval > 0` in all 10/10 panel conditions, descriptively.

Scientific positioning: the fixed-readout plus low-capacity recalibration
distinction remains the Paper-A contribution. The simple susceptibility
predictor is not supported, so the novelty claim must remain on the bounded
positive/negative evidence chain rather than a mechanism-level prediction.

## Remaining Novelty Risk

- The use of a fixed readout and featurewise calibration is conceptually
  close to low-rank/affine adaptation and readout-lens work.
- The predictive claim must remain about conditional susceptibility, not
  general coordinate transport, functional binding, or behavior.
- The study remains single-model and controlled-data unless later work
  extends it.
- The novelty depends on the separation between diagnostic and confirmatory
  partitions and on the scientific unit being condition/panel, not layers or
  items.
- If reviewers treat "predicting calibration rescue from held-out mismatch" as
  an incremental engineering metric, Paper-A will need to lean on the clean
  negative/heterogeneous evidence chain rather than overstate novelty.

## Citations Still Needed

Targeted primary-source retrieval remains incomplete for the broader layerwise
readout and representation-compatibility neighborhood. Before prose freezing,
Paper-A should still confirm and position:

- Logit Lens / other iterative readout methods adjacent to Tuned Lens;
- layer-specific affine probe/readout stability across depth;
- cross-layer representation compatibility and transport-like measures;
- representation intervention versus functional evidence;
- recent probing/decoding critiques beyond the three anchors above.

Status:

- `TUNED_LENS_POSITIONING_COMPLETE = true`
- `MODEL_STITCHING_POSITIONING_COMPLETE = true`
- `AFFINE_ALIGNMENT_NOVELTY_CLAIM = NOT_CLAIMED`
- `EXP024_SUSCEPTIBILITY_OUTCOME = NOT_SUPPORTED_BY_EXP024_PRIMARY_TEST`
- `PRIOR_ART_TARGETED_REVIEW_COMPLETE = true` for the three required anchors.
- `PRIOR_ART_SEARCH_REQUIRED = PARTIAL` for the broader surrounding literature.
