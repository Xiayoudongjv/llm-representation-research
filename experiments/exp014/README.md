# EXP-014 Gemma Steering and Relational Preservation Replication

Run the fixed, local-cache Gemma steering replication:

```bash
python experiments/exp014/gemma_steering_replication.py
```

The experiment reuses EXP-003's 24 raw plain-text prompts and applies the
predeclared beta schedule to layer-26 last-token representations. It performs
no generation and saves only aggregate metrics, summaries, and plots.
