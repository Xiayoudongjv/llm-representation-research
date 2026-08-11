# When Is a Representation Transformation Valid?

## A Probe of Task-Associated Geometry and Relational Preservation in LLM Hidden States

## 1. Abstract

This paper presents an exploratory representation-level study of hidden states
from `Qwen/Qwen3-1.7B`. We measure task-associated hidden-state geometry,
calibrated centroid steering, relational preservation using an RSM-based proxy,
and a transition-validity frontier. We then add a normal-generation
answer-level baseline, a conservative scoring audit, and an exploratory link
between representation metrics and answer difficulty. In the current
controlled setting, calibrated steering reaches target-group assignments across
tested transitions, and beta 0.75 is a stable frontier point under most
invariant-aware selection settings. The answer-level baseline has overall strict
accuracy 0.625, while the representation-behavior link remains inconclusive
because it is based on only four groups. These results do not claim
generation-time steering, reasoning improvement, true logical invariance, or a
causal relationship between representation metrics and behavior.

## 2. Introduction

Activation and representation transformations are often evaluated by whether
they move internal states toward a desired region. Movement alone is
insufficient: a transformation may reach a target centroid while distorting
the relations among the source examples. A more conservative notion of
validity should therefore consider both transition success and preservation of
relevant relational structure.

This work asks when a representation transformation should be considered
valid. It studies the question with controlled prompts, last-token hidden-state
representations, calibrated centroid steering, an RSM-based relational proxy,
and a small answer-level behavioral baseline. The results are deliberately
limited to an exploratory analysis of one model and a small manually controlled
prompt set.

## 3. Research Question

The main question is:

**When is a representation transformation valid?**

Subquestions are:

- Do task groups form measurable geometry in hidden states?
- Can calibrated centroid steering move source representations toward target task regions?
- Does steering preserve within-source relational structure?
- Is there a transition-validity frontier?
- Do representation-level indicators correspond to answer-level difficulty?

## 4. Method Overview

### Part I: Geometry

EXP-001 measures final-layer geometry, EXP-002 measures geometry across
Transformer layers, and EXP-003 adds lexical and paraphrase controls.

### Part II: Transformation

EXP-004 tests normalized static steering, EXP-004B calibrates centroid
steering strength, and EXP-005 evaluates all ordered transitions among the four
task groups.

### Part III: Validity

EXP-006 defines an RSM-based invariant violation score, EXP-007 identifies a
transition-validity frontier, and EXP-008 selects among discrete beta values
with invariant and perturbation penalties.

### Part IV: Behavioral Link

EXP-009 evaluates normal model answers, EXP-009B audits strict scoring, and
EXP-010 explores group-level correlations between answer accuracy and existing
representation metrics.

## 5. Experimental Setup

All experiments use `Qwen/Qwen3-1.7B` when a model run is required. Hidden
states are extracted from controlled prompts, with a focus on layer 16 after
the layer-wise analyses. The task groups are:

- logic
- causality
- analogy
- definition

The primary representation is the last-token hidden state. The steering
experiments operate on representations after extraction and do not intervene
during generation. EXP-009 is a normal-generation answer-level baseline only;
it applies no activation steering or hidden-state intervention.

## 6. Results

### 6.1 Task-associated Geometry

EXP-001 found final-layer PCA and cosine-similarity structure in the initial
12-prompt set. EXP-002 showed that layer-wise geometry is non-monotonic rather
than simply increasing with depth. EXP-003 retained a controlled but weak
signal after original-style and paraphrase comparisons. Layer 16 was the most
useful layer in the controlled setup for separation and later steering
analyses. These findings support cautious language about task-associated
geometry, not claims of explicit semantic categories.

### 6.2 Calibrated Representation Transformation

The normalized EXP-004 steering direction was too weak for reliable
reassignment. EXP-004B showed stronger movement with raw calibrated centroid
difference steering: beta 0.75 reached target assignment rate 1.0 for the
logic-to-causality pair. EXP-005 extended the analysis to all 12 ordered
transitions, which all reached assignment rate 1.0 by beta 0.75. The transitions
required nontrivial perturbation magnitudes, so assignment is evidence of
representation movement rather than behavioral transformation.

### 6.3 Relational Preservation and Validity Frontier

EXP-006 measures relational preservation with

`IVS = 1 - Pearson(RSM_before, RSM_after)`.

Higher beta increases target assignment but also increases IVS, while RSM
Pearson decreases. RSM is mostly preserved at the selected operating point in
the current setup, but it remains a proxy rather than a true logical invariant.
EXP-007 selected beta 0.75 as the frontier point for all 12 ordered pairs.
EXP-008 tested 24 invariant-aware lambda-gamma settings; 23/24 retained mean
beta 0.75, while the strongest penalty setting selected a slightly smaller
mean beta of 0.7292 with a small assignment loss. This reinforces beta 0.75 as
a current exploratory operating point, not a universal optimum.

### 6.4 Answer-level Baseline and Scoring Audit

EXP-009 used normal generation on 24 deterministic prompts. Strict overall
accuracy was 0.625. Group accuracies were:

| Group | Accuracy |
|---|---:|
| logic | 0.8333 |
| causality | 0.6667 |
| analogy | 0.3333 |
| definition | 0.6667 |

EXP-009B found that conservative audited upper-bound accuracy remained 0.625.
The audit labels were: strict_correct 15, likely_correct_scoring_miss 0,
partially_correct 2, ambiguous 4, and likely_wrong 3. Analogy remained the
least stable group. This scoring audit does not replace human annotation and
does not fully resolve semantic correctness.

### 6.5 Representation-Behavior Link

EXP-010 performed an exploratory group-level correlation analysis using only
four task groups. The strongest negative correlation was between strict
accuracy and `layer16_within_similarity`, with `r = -0.9122`. The strongest
positive correlation was with `mean_incoming_final_ivs`, with `r = 0.2199`.
These values are unstable with n=4 and do not provide a reliable conclusion.
Representation metrics do not currently explain answer behavior by themselves.

## 7. Discussion

The experiments distinguish representation movement from transformation
validity. A centroid shift can produce target-group assignment without showing
that the model performs a different task or preserves the relevant relations.
The RSM proxy and transition-validity frontier provide a useful framing for
measuring that trade-off, but they do not establish a complete theory of
validity.

The answer-level baseline provides an important behavioral reference, yet the
current representation-behavior link is unresolved. Answer evaluation must be
expanded and made more robust before stronger claims are considered. In
particular, the four-group correlation analysis is too small for inference and
the representation and behavior prompt sets are not fully identical.

## 8. Limitations

- Only one model is studied: `Qwen/Qwen3-1.7B`.
- The prompt sets are small, English-only, and manually controlled.
- Only four task groups are used.
- Representations use the last token only.
- The RSM score is a proxy, not a true logical invariant.
- No generation-time intervention is performed.
- No reasoning improvement claim is supported.
- No causal representation-behavior claim is supported.
- Answer scoring is small and remains limited despite the audit.
- Representation prompts and behavior prompts are not fully identical.
- Nearest-centroid assignment is not an answer-level reasoning measure.
- Large perturbations may produce out-of-distribution representations.

## 9. Conclusion

This project proposes a conservative framework for evaluating representation
transformations. A potentially valid transformation should consider both
transition success and relational preservation rather than movement alone. The
current evidence supports representation-level feasibility for calibrated
centroid transitions and identifies beta 0.75 as a useful exploratory frontier
point. It does not establish behavioral improvement, generation-time steering,
true logical invariance, or causal representation-behavior relationships.

The next step is an expanded answer-level evaluation, followed only later by a
carefully controlled intervention study.

## 10. Claims

| Claim | Status | Evidence | Allowed wording |
|---|---|---|---|
| Hidden-state representations can be extracted and compared in this setup | Supported | EXP-000B to EXP-003 | “The pipeline measures hidden-state representations in Qwen/Qwen3-1.7B.” |
| Task-associated geometry is present | Partially supported | EXP-001 to EXP-003 | “Controlled prompts show exploratory task-associated geometric patterns.” |
| Calibrated steering induces representation-level transitions | Supported | EXP-004B and EXP-005 | “Calibrated centroid steering reaches target-group assignments in the tested representation space.” |
| Beta 0.75 is a stable frontier point here | Partially supported | EXP-006 to EXP-008 | “Beta 0.75 is a stable exploratory operating point in this setting.” |
| RSM preservation measures true logical invariance | Not supported | IVS is a proxy | “RSM correlation is used as a relational-preservation proxy.” |
| Representation metrics explain answer difficulty | Not supported | EXP-010, n=4 | “The representation-behavior relationship remains inconclusive.” |
| Steering improves reasoning | Not supported | No intervention or answer comparison | Do not claim reasoning improvement. |
