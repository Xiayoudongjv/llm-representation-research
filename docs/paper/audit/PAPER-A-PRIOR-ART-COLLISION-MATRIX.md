# Paper-A Prior-Art Collision Matrix

Status: `PRIOR_ART_AUDIT_ARTIFACT_PA_NOVELTY_001`
Legend: `Y` = present/established, `P` = partial or related, `N` = not found or not central.

| Prior work | Fixed readout | Source x target matrix | Distance effect | Source effect | Target effect | Source-target asymmetry | Recalibration | Cross-model comparison | Prospective test | Profile construction | Profile dissociation | Mechanistic interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Logit Lens (nostalgebraist 2020) | Y | N | Y | N | N | N | N | P | N | N | N | P |
| Tuned Lens (Belrose et al. 2023) | Y | N | Y | N | N | N | P | P | N | N | N | Y |
| Patchscopes (Ghandeharioun et al. 2024) | P | N | P | N | N | N | N | P | N | N | N | Y |
| Revisiting Model Stitching (Bansal et al. 2021) | N | P | P | P | P | P | Y | Y | N | N | N | P |
| Similarity and Matching (Csiszarik et al. 2021) | N | P | P | P | P | P | Y | Y | N | N | N | P |
| SVCCA (Raghu et al. 2017) | N | P | Y | P | P | P | Y | P | N | N | N | N |
| CKA (Kornblith et al. 2019) | N | P | Y | P | P | P | Y | P | N | N | N | N |
| Insights on Representational Similarity (Morcos et al. 2018) | N | P | Y | P | P | P | Y | P | N | N | N | N |
| Latent Space Translation (Maiorca et al. 2023) | N | N | N | P | P | P | Y | Y | N | N | N | N |
| Functional Alignment Can Mislead (Smith et al. 2025) | P | N | N | N | N | N | Y | Y | N | N | N | Y |
| How Not to Stitch (Balogh & Jelasity 2025) | N | Y | Y | P | P | Y | Y | N | N | N | N | Y |
| Transferring Linear Features Across LMs (Chen et al. 2025) | N | N | P | P | P | P | Y | Y | N | N | N | P |
| Tracing Representation Progression (Jiang et al. 2024) | Y | N | Y | N | N | N | N | P | N | N | N | P |
| Causality != Decodability (Huang & Chang 2025) | P | N | P | N | N | N | N | N | N | N | N | Y |
| Fresh-Head Probe (TMLR/OpenReview 230T2UcWwR) | Y | N | N | N | N | N | Y | N | N | N | N | Y |
| How Do LLMs Use Their Depth? (Gupta et al. 2025) | N | N | Y | N | N | N | N | Y | N | N | N | Y |
| Do LMs Use Their Depth Efficiently? (Csordas et al. 2025) | N | N | Y | N | N | N | N | Y | N | N | N | Y |
| Do Transformers Use Their Depth Adaptively? (Curth et al. 2026) | P | N | Y | N | N | N | N | P | N | N | N | Y |
| Where meaning lives (Tikhomirova & Wulff 2026) | P | N | Y | P | P | N | N | Y | N | N | N | N |
| Multi-Level Optimal Transport (Shah & Khosla 2026) | N | Y | P | P | P | Y | Y | Y | N | N | N | N |
| SemRF (Gu et al. 2026) | Y | N | Y | P | P | Y | P | P | N | P | N | Y |
| Paper A current contribution | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | P |

## Strongest Collision

`SemRF` is the strongest current collision. Its abstract explicitly frames intermediate decoding as requiring comparable readout coordinates across layers and states that apparent motion may reflect measurement drift rather than computation. This independently attacks a central fixed-readout interpretation and reinforces Paper-A's decodability/causal-role boundary, but it does not reproduce the three-model registered source/target x recalibratability dissociation.
