# Claims Checklist v0.5

## Supported

- Controlled task-associated geometry was observed in two small LLM families.
- A paraphrase-controlled signal was observed in both models under the current
  24-prompt design.
- Calibrated representation transitions were observed in both models.
- Stronger positive steering increased perturbation and relational disruption
  in both models.
- Layer profile and steering operating point were model-dependent.
- The frozen Qwen behavioral baseline does not support a reliable
  representation-to-answer-difficulty inference.

## Partially Supported

- The transition-plus-relational-preservation evaluation framing extends beyond
  a single model in these two settings.
- The controlled paraphrase signal is robust across the two evaluated models.
- Qwen's beta-0.75 frontier had a partial counterpart in Gemma: it reached
  mean assignment 0.875, but Gemma's exploratory rule selected beta 1.0.

## Not Supported

- A model-invariant hidden-state geometry across language models.
- A model-invariant steering frontier or fixed beta operating point.
- Geometry as a cause of task difficulty.
- Representation steering as an improvement to reasoning.
- A working generation-time intervention.
- RSM as a true logical invariant.
- Extension of these findings to substantially larger or frontier-scale models.
