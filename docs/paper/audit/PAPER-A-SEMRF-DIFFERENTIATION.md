# Paper-A SemRF Differentiation

Status: `PA_NOVELTY_002_SEMRF_DIFFERENTIATION`
Strongest prior-art collision: `SemRF: A Semantic Reference Frame for Residual-Stream Dynamics in Language Models`, arXiv:2606.32022.

## High-Resolution Comparison

| Dimension | SemRF | Paper-A |
| --- | --- | --- |
| Scientific question | How should semantic measurement be separated from residual dynamics so apparent motion is not drift? | Do shared distance-associated compatibility profiles imply shared source/target organization and recalibratability across models? |
| Representation object | Residual-stream states measured against fixed semantic anchors | Hidden states at registered carrier locations across normalized depth |
| Source role | Semantic anchors/frame source | Source layer in a fixed-readout compatibility matrix |
| Target role | Residual state measured against anchors | Target layer in a fixed-readout compatibility matrix |
| Readout/training rule | Anchor-based coordinates; pseudo-inverse tying and bi-invertibility conditions | Fixed semantic-class readout frozen on FIT; no layer-specific refit |
| Matrix or pair structure | Layerwise steps, contribution profiles, Voronoi trace | Full source x target compatibility matrix and SDI decomposition |
| Distance analysis | Trace path, step, curvature, profile mismatch | Distance-associated compatibility structure and registered support |
| Source effect | Anchor/frame definition and interface error | Source-layer variance contribution to SDI |
| Target effect | Measurement projection/residual | Target-layer variance contribution to SDI |
| Source-target interaction | Frame/readout synchronization | Explicit two-way SDI source-target decomposition |
| Calibration/realignment | Pseudo-inverse tying and stable anchor coordinates | LOW-D featurewise/moment recalibration under FIT-only rule |
| Cross-model comparison | Not a three-model registered profile comparison | Qwen, OLMo, Llama registered profiles |
| Profile construction | Semantic traces, imbalance diagnostics, knowledge density | Distance structure + SDI + LOW-D profile |
| Dissociation result | Separates semantic measurement from residual dynamics | Separates distance structure, source/target organization, recalibratability across models |
| Prospective validation | Not identified as a prospective third-model test | EXP-027 third-model routing frozen before outcome |
| Claim scope | Formal semantic-frame conditions and trace bounds | Narrow three-model empirical profile dissociation |

## What SemRF Already Establishes

- Intermediate decoding requires comparable readout coordinates across layers.
- If frame and readout disagree, apparent residual motion may reflect measurement drift.
- Fixed semantic frames and anchor-based synchronization are a useful formalization.
- Readout/frame mismatch must be controlled before interpreting residual dynamics.

## What Paper-A Must Not Reclaim

- "Measurement frames can differ across layers."
- "Fixed-readout degradation can be readout/frame mismatch rather than information loss."
- "Apparent residual motion may be measurement drift."
- "Anchor/frame synchronization matters for semantic measurement."

## What Paper-A Adds, If Any

- A registered full source x target compatibility matrix with explicit source/target dominance and LOW-D recalibration dimensions.
- A three-model empirical profile comparison: Qwen, OLMo, and Llama.
- A prospective third-model test in which Llama combines Qwen-like target dominance with OLMo-like supported LOW-D recovery.
- Evidence that distance-associated compatibility structure is shared while the other two dimensions combine differently, within this operational framework.

## Substantive vs Terminological

The remainder is substantive but moderate, not strong. SemRF removes Paper-A's ability to claim novelty for measurement-frame/drift concerns. Paper-A's narrow residual is the cross-model profile dissociation, which SemRF does not reproduce. The distinction is not merely terminological, but it is also not a large mechanistic advance.

## Other Major Collisions

| Prior work | What it establishes | Paper-A boundary |
| --- | --- | --- |
| Tuned Lens | Per-block affine probes decode across depth | Paper-A uses a fixed readout and LOW-D recalibration; no novelty for layer-specific decoding |
| Patchscopes | Hidden states can be inspected through patchable decoding scopes | Paper-A does not claim new decoding scope; carrier control is a comparability rule |
| Chen et al. 2025 affine stitching | Affine residual-stream mappings transfer features across models | Paper-A's LOW-D recalibration is operational, not a new feature-transfer contribution |
| Shah & Khosla 2026 HOT | Soft layer-to-layer couplings and global alignment | Paper-A's SDI is a simpler two-way summary; no novelty for alignment frameworks |
| Csordas/Gupta/Curth depth work | Depth usage and layerwise dynamics are established | Paper-A cannot claim depth-distance structure as first discovery |

## Differentiation Verdict

- `SEMRF_DIFFERENTIATION = MODERATE`
- `SEMRF_COLLISION_FATAL = false`
- `REMAINDER = cross-model source/target organization x recalibratability dissociation, with prospective third-model evidence.`
