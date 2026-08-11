# EXP-008 Update Note

## Why EXP-008 Was Needed

EXP-006 showed that calibrated steering increases target assignment while also
increasing the RSM-based invariant violation score and perturbation. EXP-007
identified beta 0.75 as a stable frontier point. EXP-008 tests whether adding
explicit invariant and perturbation penalties changes that operating point.

## What It Tested

EXP-008 reused the existing EXP-006 and EXP-007 CSV results. For each ordered
source-target pair and each of 24 lambda-gamma settings, it selected among the
already tested discrete beta values using assignment rate minus weighted IVS and
relative perturbation. It did not rerun Qwen and did not learn a new steering
transformation.

## Main Result

Twenty-three of 24 settings selected mean beta 0.75, and 23 of 24 settings
reached assignment rate 1.0 for all 12 pairs. Only lambda=100, gamma=0.2 was
more conservative: mean beta 0.7292, mean assignment 0.9722, mean IVS 0.002585,
and mean relative perturbation 0.334954.

## Interpretation

Beta 0.75 is robust under most tested invariant-aware selection settings. A
smaller beta can reduce measured IVS and perturbation, but the tested strong
penalties caused a small assignment loss.

## Why This Does Not Prove Generation-time Validity

The analysis selects points in precomputed hidden-state metrics. It does not
modify activations during generation, measure generated answers, test answer
correctness, or establish true logical invariance. RSM correlation remains a
proxy, and the result is limited to the studied model and prompt setting.
