# Cross-Model Summary

This table synthesizes results from Qwen/Qwen3-1.7B and google/gemma-3-1b-it.
It describes representation-level observations across two small LLMs.

| Finding | Qwen | Gemma | Replication status | Interpretation |
|---|---|---|---|---|
| Task-associated geometry | Positive controlled structure; strongest signal around layer 16 | Positive controlled structure across multiple nonembedding layers | Replicated | The current controlled prompt groups separate in both models. |
| Paraphrase-controlled signal | Peak retention 0.036424 at layer 16 | Peak retention 0.071401 at layer 26 | Replicated | Same-group paraphrases remained relatively closer than cross-group controls at positive layers. |
| Non-monotonic layer profile | Signal rises then weakens after its mid-depth peak | Separation rises sharply at the final index; silhouette peaks earlier | Replicated | Both depth profiles vary, but not monotonically. |
| Mid/mid-deep peak | Strongest controlled signal around layer 16 | Strongest separation and retention at final layer 26 | Not replicated | The peak depth is model-dependent. |
| Calibrated steering | Target-directed movement under centroid steering | Target-directed movement under centroid steering | Replicated | Both models show representation-level transitions. |
| Multi-pair steering | 12/12 transitions reached full assignment by beta 0.75 | 12/12 transitions eventually reached full assignment | Replicated | The effect is not limited to one ordered pair in either model. |
| Perturbation tradeoff | Larger beta increased movement and relative perturbation | Larger beta increased movement and relative perturbation | Replicated | Stronger transitions require larger representation changes. |
| Relational-preservation tradeoff | IVS rises and RSM Pearson falls with beta | IVS rises and RSM Pearson falls with beta | Replicated | The RSM proxy shows increasing relational disruption at stronger steering. |
| Beta 0.75 frontier | Mean assignment 1.000; mean IVS 0.002850 | Mean assignment 0.875; mean IVS 0.017970 | Partially replicated | A useful operating point exists in both settings, but its beta differs. |
| Behavioral validation | Frozen Qwen baseline: 60/80 = 0.750 | No behavioral benchmark yet | Not assessed across models | No cross-model behavior conclusion is available. |

## Interpretation Boundary

The replicated findings concern controlled representations and in-memory
centroid transformations. They do not establish generation-time effects,
behavioral improvement, or an exhaustive account of relational structure.
