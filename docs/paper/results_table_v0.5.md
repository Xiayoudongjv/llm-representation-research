# Results Table v0.5

| Experiment | Model | Contribution | Key result |
|---|---|---|---|
| EXP-003 | Qwen3-1.7B | Controlled geometry | Layer 16: separation 0.073015, silhouette 0.182165, retention 0.036424. |
| EXP-005 | Qwen3-1.7B | Multi-pair steering | All 12 ordered transitions reached full target assignment by beta 0.75. |
| EXP-006 | Qwen3-1.7B | RSM-preservation proxy | Stronger beta increased transition success and IVS while reducing RSM Pearson. |
| EXP-007 | Qwen3-1.7B | Exploratory validity frontier | All 12 pairs selected beta 0.75; mean IVS 0.002850 and mean RSM Pearson 0.997150. |
| EXP-008 | Qwen3-1.7B | Invariant-aware selection | 23/24 penalty settings retained mean selected beta 0.75. |
| EXP-013 | Gemma-3-1B-IT | Controlled geometry replication | Separation 0.093294 and retention 0.071401 at layer 26; silhouette 0.139718 at layer 16. |
| EXP-014 | Gemma-3-1B-IT | Steering and RSM replication | All 12 transitions eventually reached full assignment; exploratory beta 1.0. |
| EXP-011D | Qwen3-1.7B | Frozen behavioral baseline | 60/80 = 0.750; causality 0.950, definition 0.850, logic 0.750, analogy 0.450. |
| EXP-012 | Qwen3-1.7B | Frozen behavior-link reanalysis | Correlations were benchmark-sensitive; n=4 cannot support reliable inference. |

## Cross-model operating-point comparison

| Quantity | Qwen3-1.7B | Gemma-3-1B-IT |
|---|---:|---:|
| Primary steering layer | 16 | 26 |
| Mean assignment at beta 0.75 | 1.000 | 0.875 |
| Mean IVS at beta 0.75 | 0.002850 | 0.017970 |
| Exploratory selected beta | 0.75 | 1.0 |

The table describes two model-specific experimental settings. It does not
compare behavior across models, because Gemma has no behavioral baseline here.
