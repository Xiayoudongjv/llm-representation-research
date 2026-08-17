# Current Research Handoff

This file is a navigation and status snapshot, not an independent source of
scientific truth. Resolve conflicts in this order: frozen configs/manifests and
hashes; result artifacts; validators; Git commits; canonical experiment docs;
this handoff; historical discussion. Preserve and report conflicts rather than
silently reconciling them.

## 1. Project Research Question

The central question is conservative: a target-associated hidden-state
transition can be independently validated at the representation level. What
stronger conclusions, if any, does that license about functional or behavioral
control?

```text
task-associated representation
        -> independently validated transition
        -> ?
        -> task-specific behavior
```

The missing link remains an open research problem.

## 2. Evidence State

### Supported

- EXP-018 supports held-out, fit/eval-separated, probe-evaluated
  target-directed representation movement on its fixed controlled design.
  TASK exceeded matched-norm random and opposite controls on the frozen probe
  comparisons. This is not evidence of a true cognitive space, behavioral
  control, reasoning improvement, or a universal task manifold.

### Not supported

- EXP-018 did not validate task-specific relational/RSM/IVS preservation.
  RSM/IVS remains a generic perturbation diagnostic, not a validated semantic
  invariant.
- EXP-017 did not support a stable task-specific correctness-level behavioral
  advantage over matched-norm random. Its frozen judgment is
  `behavioral_effect = FAILED`, `representation_behavior_link = NOT_SUPPORTED`,
  and `STOP_AFTER_NEGATIVE`. This does not establish a universal
  representation/behavior dissociation.

### Failed measurement validation and unresolved outcome

- EXP-019's frozen output-only evaluator failed its one-shot independent
  Final-200 criteria: balanced accuracy 0.4850, macro F1 0.4580, accuracy
  0.4850; recalls were logic 0.26, causality 0.26, analogy 0.84, and definition
  0.58. Decision: `FAILED_INDEPENDENT_GENERALIZATION`.
- This is a measurement-validation failure. It does not show that EXP-017
  output targetness did not change. Output-level behavioral targetness remains
  `UNRESOLVED`, and `EXP017_TARGETNESS_UNLOCKED = false`.
- Final-200 has been outcome-inspected once. It may support descriptive error
  analysis or hypotheses, but it is no longer an untouched confirmatory set for
  any evaluator redesigned after those results.

## 3. What Is Not Established

The repository does not establish reasoning improvement, behavioral task
conversion, cognitive task spaces, latent task manifolds, semantic relational
invariants, active downstream correction, universal scale effects, or a
general causal representation-to-behavior link.

## 4. Current Claim Boundary

Currently allowed:

- task-associated geometry is observable in this controlled setup;
- a centroid-derived direction produced independently validated held-out
  target-directed representation transition in EXP-018;
- representation transition alone did not establish task-specific behavioral
  control in EXP-017;
- relational/invariant specificity was not supported;
- EXP-019 procedural performance did not generalize to frozen Final-200; and
- output-level task targetness therefore remains unresolved.

Currently forbidden without new evidence:

- steering improves reasoning;
- hidden-state transition causes task conversion;
- task clusters are proven cognitive spaces or latent task manifolds;
- RSM/IVS is a validated semantic invariant;
- EXP-019 proves behavioral targetness did not change;
- representation and behavior are universally dissociated;
- downstream layers actively correct steering; or
- higher model scale necessarily changes representation/behavior coupling.

## 5. Current EXP-020 State

EXP-020A scientific status is `NOT_STARTED`; no formal Qwen3-4B task prompt or
scientific representation outcome exists. Task 080 has already frozen and
committed the confirmatory protocol at Git commit
`ea85fa5bfb17d8c684da619fe6cd74418c2312be`.

The frozen protocol uses primary block 18 / `hidden_states[19]`, secondary
descriptive block 26 / `hidden_states[27]`, primary beta 0.75, fit-only
direction construction and probe fitting, held-out EVAL prompts, matched-random
and opposite controls, and a non-rescuable primary gate. The machine-readable
config and validator are authoritative.

## 6. Model and Hardware Qualification

- Model: `Qwen/Qwen3-4B`
- Revision: `1cfa9a7208912126459214e8b04321603b3df60c`
- Canonical path: `D:\Qwen3-4B-transfer`; local files only
- Architecture: `Qwen3ForCausalLM` / `qwen3`
- Hidden size / blocks / vocabulary: 2560 / 36 / 151936
- Selected mode: native BF16 on `cuda:0`; no offload or quantization required
- Peak forward allocation: 7.5339 GiB
- Hidden-state diagnostic: 37 entries (embedding plus 36 block outputs)
- Zero hook: `ZERO_HOOK_EQUIVALENCE_PASS`, maximum logit difference 0.0

## 7. Contamination / Access Boundaries

- EXP-017 aggregate correctness evidence is part of the historical record.
  Raw EXP-017 generations remain outside any unlocked output-targetness
  analysis and must not be inspected to choose EXP-020 parameters, prompts,
  layers, betas, transitions, or metrics.
- EXP-019 and Final-200 must not be modified or used to rescue the failed
  evaluator. A future evaluator needs a new untouched confirmatory set.
- EXP-020A must use only its frozen prompt IDs, hashes, split, layers, beta,
  controls, probe policy, statistics, and stop rules. No outcome-based item
  filtering or favorable-subset success redefinition is allowed.

## 8. Scientific Process Rules

For every future experiment, keep four levels separate:

1. **Observation:** measured fact, such as a probability decreasing downstream.
2. **Operational result:** whether a preregistered criterion was met.
3. **Interpretation:** a bounded reading compatible with the result.
4. **Speculation:** an untested mechanism, such as compensation or overwrite.

Also preserve preregistration before outcome inspection; fit/eval separation;
negative results; infrastructure/measurement/scientific failure distinctions;
no post-hoc layer or beta rescue; no outcome-based filtering; no modification
of frozen independent sets after inspection; controls before mechanistic
interpretation; and the principles that failed measurement does not imply
absence of a phenomenon, decodability does not imply functional role, and
publication value does not determine scientific outcomes.

## 9. Current Git State

The audited base state before this handoff was written was clean
`main...origin/main` at
`ea85fa5bfb17d8c684da619fe6cd74418c2312be`. The Task 079C handoff commit will
necessarily advance HEAD; use Git history to identify that commit.

Continuity conflict: the Task 079C request expected `e71ecc0...` and said Task
080 was pending. Git and frozen artifacts show that Task 080 was subsequently
completed at `ea85fa5...`. The repository state is authoritative.

## 10. Immediate Next Gate

Task 080 is complete, but EXP-020A has not run. The next gate is a separately
authorized implementation/preflight against the already frozen protocol,
followed by formal EXP-020A execution only under that protocol. Before any
scientific outcome generation, the dedicated validator and every frozen
pre-run sanity check must pass. This handoff does not authorize execution.

Conditional possibilities—EXP-020B behavior, downstream persistence,
timing decomposition, a harness closed-loop pilot, or a task-functional-
dimension project—are not scheduled. Each needs evidence-based justification,
measurement-validity review, preregistration, and explicit stop rules.

## 11. Hypothesis Backlog Pointer

Untested explanations and possible discriminating studies are indexed in
[HYPOTHESIS-BACKLOG.md](research/HYPOTHESIS-BACKLOG.md). They are hypotheses,
not findings or automatically planned experiments.

## 12. Canonical Source Documents

- EXP-018: [frozen conditions](../experiments/exp018/validation_conditions.json),
  [canonical report](experiments/EXP-018.md), and
  [probe results](../results/exp018/probe_metrics.csv)
- EXP-017: [frozen amended conditions](../experiments/exp017/intervention_conditions_v2.json),
  [canonical report](experiments/EXP-017.md), and
  [canonical EXP-017 authority](experiments/EXP-017.md)
- EXP-019: [freeze manifest](../experiments/exp019/data/final200_freeze_manifest.json),
  [one-shot metrics](../experiments/exp019/results/final200_metrics.json), and
  [canonical report](experiments/EXP-019.md)
- EXP-020A: [frozen config](../experiments/exp020/exp020_frozen_config.json),
  [preregistration](experiments/EXP-020-PREREGISTRATION.md),
  [validator](../experiments/exp020/validate_exp020_preregistration.py), and
  [hardware qualification](../experiments/exp020/results/qwen3_4b_hardware_qualification.json)
- Current synthesis: [evidence map](paper/evidence_map_v0.7.md),
  [claim checklist](paper/claims_checklist_v0.7.md), and
  [project status](paper/project_status_v0.7.md)
- Hypotheses: [backlog](research/HYPOTHESIS-BACKLOG.md)

Note: `results/exp018/validation_summary.json` contains planned counts rather
than the scientific outcome summary; do not treat it alone as the EXP-018
result.
