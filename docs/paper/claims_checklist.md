# Claims Checklist

## Claims Supported by Current Evidence

- Hidden states from `Qwen/Qwen3-1.7B` can be extracted locally with the project pipeline.
- Controlled prompts show task-associated geometric patterns in selected hidden-state representations.
- Geometry varies across tested Transformer layers; layer 16 often showed stronger controlled separation in these experiments.
- Calibrated centroid steering can induce representation-level nearest-centroid transitions for the tested ordered group pairs.
- RSM-based IVS provides a measurable proxy for within-source relational preservation during representation-level steering.
- Beta 0.75 is a stable exploratory operating point for the current model, layer, prompt set, centroid method, and frontier rule.

## Claims Not Yet Supported

- Steering improves reasoning ability.
- Generation-time steering works.
- True semantic latent spaces are proven.
- Logical invariants are preserved.
- Results generalize to other models.
- Results generalize to larger or naturalistic datasets.
- A task-conditioned learned transformation is better than centroid steering.
