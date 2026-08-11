# Claims Checklist v0.3

## 1. Supported Claims

- The project can extract and compare last-token hidden-state representations from `Qwen/Qwen3-1.7B`.
- Calibrated centroid steering produces representation-level target-group assignments for the tested prompt groups and transitions.
- EXP-006 provides a computable RSM-based invariant violation proxy.
- The answer-level baseline and scoring audit can be reproduced from the saved outputs.
- Shared IO, extraction, plotting utilities and tests now provide basic engineering infrastructure.

## 2. Partially Supported Claims

- **Task-associated geometry:** observed in controlled prompts, but small and model-specific.
- **Validity frontier:** beta 0.75 is stable in the current setting, not a universal optimum.
- **Relational preservation:** RSM correlation measures a useful proxy, not the full relational concept.
- **Behavioral relevance:** exploratory correlations exist, but n=4 groups is insufficient.

## 3. Unsupported / Forbidden Claims

- Steering improves reasoning.
- Generation-time steering works.
- The LLM has an explicit cognitive geometry.
- RSM is a true logical invariant.
- Representation metrics explain answer difficulty.
- Results generalize to all LLMs.
- Representation-level transitions imply semantic task conversion.

## 4. Safe Paper Wording

- “exploratory representation-level analysis”
- “task-associated geometric pattern in the controlled prompt set”
- “calibrated centroid steering in the selected representation space”
- “RSM-based proxy for relational preservation”
- “beta 0.75 is a stable exploratory operating point in this setting”
- “the representation-behavior relationship remains inconclusive”

## 5. Unsafe Paper Wording

Avoid:

- “steering improves reasoning”
- “the model reasons in a semantic latent space”
- “the transformation preserves logical invariants”
- “generation-time intervention is validated”
- “representation metrics predict behavior”
- “the result generalizes to LLMs”
