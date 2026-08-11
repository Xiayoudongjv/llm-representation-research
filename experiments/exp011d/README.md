# EXP-011D Behavioral Benchmark Freeze

Apply only EXP-011C-approved lexical or wording additions to the EXP-011
acceptable-answer vocabulary, then rescore existing EXP-011B answers offline.

```bash
python experiments/exp011d/apply_audit_patches_and_rescore.py
```

The script does not run or load Qwen. It preserves every model answer and does
not grant partial credit or promote ambiguous answers.
