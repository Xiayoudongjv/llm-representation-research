# EXP-011C Expanded Answer Scoring Audit

This offline audit reviews existing EXP-011B answers without rerunning Qwen.
It labels each answer conservatively and separates strict accuracy from a
limited scoring-coverage adjustment.

```bash
python experiments/exp011c/audit_expanded_answers.py
```

Outputs include per-item labels, group metrics, label counts, a summary, and a
strict-versus-audited group plot. No model, logits, or hidden states are used.
