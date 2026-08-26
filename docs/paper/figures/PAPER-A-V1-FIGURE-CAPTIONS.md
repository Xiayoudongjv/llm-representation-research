# Paper A V1 Figure Captions

## Figure 1 — Operational measurement framework

**What is shown.** A readout fit at source depth `s` is evaluated on the source self representation and then directly reused on target depth `t`. The target representation branches into direct reuse through frozen `q_s` and a separate restricted calibration path whose parameters are estimated on FIT only, frozen, and then applied to EVAL, yielding `C0`, `D`, `C_cal`, and `R` as parallel operational quantities.

**Main observation.** These are distinct operational measurements of the same source-target protocol.

**Not implied.** The diagram does not represent latent geometry, information flow, mechanism, causality, or semantic equivalence.

## Figure 2 — Three-model operational profiles

**What is shown.** Registered continuous values and one-sided 95% cluster-bootstrap intervals for depth-distance association with degradation, SDI, and LOW-D restricted recovery. Panel D is a discrete 2×2 display of the observed combinations of registered profile components.

**Main observation.** Positive distance-associated structure is supported in all three tested models; organization and LOW-D recovery classifications differ by model. The third registered profile adds a target-dominant plus supported LOW-D combination absent from the initial two-model pairing.

**Not implied.** Categorical profiles are not a learned embedding, latent coordinate space, clustering, taxonomy, independence test, or causal explanation. The empty cell means not observed in this three-model panel. Llama routing was prospective; the mapping-break interpretation is bounded post-hoc synthesis.

## Figure 3 — Full directed source-target matrices

**What is shown.** Native-resolution condition-pooled degradation matrices `Dbar_eval`, with source-readout layers on rows and target-representation layers on columns. Qwen uses 28 layers; OLMo and Llama use 16 layers. Panels retain native layer indices. A common symmetric color scale is used only for visual comparison, with no interpolation or resampling. Cross-model distance analysis uses registered normalized depth. `D = 0` means no degradation relative to the source self condition; positive `D` means worse direct fixed-readout compatibility relative to self.

**Main observation.** The registered operational matrix retains source-target orientation and permits descriptive comparison of depth-dependent degradation.

**Not implied.** Matrix orientation is operational; it does not establish geometry, information flow, causal direction, or a mechanism. The heatmaps do not replace the separate `C0`, `D`, and `R` definitions.
