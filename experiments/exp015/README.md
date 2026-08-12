# EXP-015 Layer-Validity Pilot

Run the fixed local-cache pilot:

```bash
python experiments/exp015/layer_validity_pilot.py
```

The pilot compares three predeclared hidden-state indices in each model over
three fixed positive beta values. It evaluates in-memory centroid steering only
and writes aggregate metrics, summaries, and plots; no generated text or raw
hidden states are saved.
