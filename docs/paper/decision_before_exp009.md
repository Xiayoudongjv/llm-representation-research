# Decision Before EXP-009

## Question

What should EXP-009 test next?

## Option A: Answer-level reasoning evaluation

- **Goal:** Test whether representation-level transitions and validity scores relate to task outcomes or answer correctness.
- **Value:** Directly connects the current hidden-state evidence to the intended reasoning question.
- **Difficulty:** Moderate; requires carefully designed answer-level prompts, scoring, controls, and evaluation protocol.
- **Risk:** The small prompt set and model-specific geometry may not predict behavior, yielding weak or null results.
- **Recommendation:** Choose this option first.

## Option B: Generation-time intervention

- **Goal:** Apply steering during model generation and measure changes in generated answers.
- **Value:** Tests whether representation movement can affect behavior in the deployed computation path.
- **Difficulty:** High; requires reliable activation hooks, intervention timing, decoding controls, and careful safety checks.
- **Risk:** Technical intervention effects may be confounded with decoding or out-of-distribution activations before the representation-to-answer link is established.
- **Recommendation:** Defer until answer-level evaluation defines a meaningful behavioral target.

## Option C: Multi-model replication

- **Goal:** Repeat the geometry, steering, and validity analyses across additional models.
- **Value:** Tests whether the observed operating point is model-specific or more broadly reproducible.
- **Difficulty:** High; model architectures, layer conventions, tokenizers, and hidden-state scales differ.
- **Risk:** Replication may be expensive and may obscure the unresolved question of whether the current metrics predict task outcomes.
- **Recommendation:** Pursue after an answer-level protocol is established, or as a later parallel study.

## Final Recommendation

EXP-009 should be **answer-level reasoning evaluation**, not generation-time
intervention yet. It directly tests whether representation-level validity relates
to task outcomes while avoiding the extra complexity of generation-time
activation hooks. Stronger claims should remain deferred until that connection
is measured.
