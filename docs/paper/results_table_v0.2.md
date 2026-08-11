# Results Table v0.2

| Experiment | Purpose | Key Result | Interpretation | Limitation |
|---|---|---|---|---|
| EXP-001 | Final-layer geometry | PCA and similarity structure observed in 12 prompts | Initial task-associated geometry signal | Small, manually designed prompt set |
| EXP-002 | Layer-wise geometry | Layer 16 had highest separation; layer 4 highest silhouette | Geometry varies with depth | Metrics are exploratory and prompt-dependent |
| EXP-003 | Lexical/paraphrase control | Layer 16 retained controlled separation; norm/token correlation near -0.005 | Signal is not explained by the measured token-count effect alone | Manual English controls do not remove all confounds |
| EXP-004 | Normalized steering baseline | Weak directional movement toward target group | Direction alone gives limited reassignment | Representation-level only |
| EXP-004B | Calibrated steering | Beta 0.75 reached target assignment rate 1.0 in the tested pair | Calibration strengthens movement | Perturbation is nontrivial |
| EXP-005 | Multi-pair generalization | All 12 ordered pairs reached assignment rate 1.0 by beta 0.75 | Effect is consistent across the four groups in this setup | One model and finite prompt set |
| EXP-006 | Relational invariant proxy | IVS rises and RSM Pearson falls with beta | Assignment and preservation trade off | RSM is only a proxy |
| EXP-007 | Transition-validity frontier | All pairs recommended beta 0.75; mean IVS about 0.00285 | Beta 0.75 is a stable exploratory point | Not a universal optimum or behavioral result |
| EXP-008 | Invariant-aware selection | 23/24 settings kept mean beta 0.75; strong penalties gave mean 0.7292 | Frontier is robust; smaller beta is a conservative alternative | Discrete selection, no learned constrained transform |
