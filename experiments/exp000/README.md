## EXP-000: Hidden State Extraction

EXP-000 establishes a reproducible baseline for loading an open-source causal
language model and extracting hidden states for one prompt. EXP-000B records
metadata only; full hidden-state tensors are intentionally not committed.

Run a syntax check from the repository root:

```bash
python -m compileall src experiments
```

Run with Qwen:

```bash
python experiments/exp000/extract_hidden_states.py --model_name Qwen/Qwen3-1.7B
```

Run with the fallback model:

```bash
python experiments/exp000/extract_hidden_states.py --use_fallback
```

Expected output includes the hidden state count and one shape, dtype, and
device line for each layer. Metadata is written to
`results/exp000/hidden_states_metadata.json`; full tensors are not saved.
