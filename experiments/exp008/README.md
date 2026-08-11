# EXP-008 Invariant-constrained Steering

This experiment selects steering strengths from the existing EXP-006 and
EXP-007 results. It does not rerun Qwen or learn a new transformation.

Run:

```bash
python experiments/exp008/invariant_constrained_selection.py
```

The constraint score is:

`target_assignment_rate - lambda * invariant_violation_score - gamma * relative_perturbation_norm`

The analysis compares the selected beta with the EXP-007 frontier beta. RSM
correlation is treated as a proxy invariant, and all conclusions remain at the
representation level.
