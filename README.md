# LLM Representation Research

Research on representation geometry, task-conditioned transformations, and relational invariants in transformer language models.

This README is a public overview and navigation surface. Canonical scientific authority lives in the linked research and experiment documents below, not in this file.

## Project Purpose

This project asks a conservative empirical question: when a task-associated hidden-state transition can be validated at the representation level, what does that license about functional or behavioral control?

The program works from measurable representation structure toward local manipulation, then toward transport, invariant preservation, and behavior.

## Conceptual Framework

```text
Representation -> Local Geometry -> Manipulation -> Transport -> Invariant Preservation -> Functional Binding -> Behavior
```

Workflow shorthand:

```text
Identify -> Manipulate -> Transport -> Propagate -> Bind -> Realize
```

This framework is conceptual. Only the earlier representation/manipulation portion currently has strong local evidence; later stages are not yet established end-to-end.

## Current Stage

Representation-level manipulation has replicated under frozen same-family, higher-parameter controls. Behavioral linkage remains unsupported. Clean-state layerwise readout transport diagnosis is the next preregistered step.

EXP-022A is scientifically ready to freeze, but it has not yet been frozen or run.

## Experiment Progression

| Experiment | Topic | Status | One-line conclusion or purpose |
| --- | --- | --- | --- |
| EXP-017 | Behavior-level pilot | `COMPLETED` | TASK intervention did not outperform matched-random control on overall correctness; representation-behavior link not supported. |
| EXP-018 | Held-out representation validation | `COMPLETED` | Strong target-directed representation movement under controlled intervention; local manipulability supported, relational/invariant gate failed. |
| EXP-019 | Independent output evaluator | `COMPLETED` | Generalization criterion failed; output-level behavioral targetness remains unresolved. |
| EXP-020A | Same-family higher-parameter replication | `COMPLETED / VALID` | Representation replication supported under frozen controls. |
| EXP-021 | Stage-Q clean-state layerwise source-class readout qualification | `COMPLETED` | Q3 technically valid but `QUALIFICATION_FAILED`; fixed reference readout did not remain qualified across all required clean checkpoints in both complementary splits. |
| EXP-022A | Clean-state layerwise readout transport diagnosis | `READY_TO_FREEZE / NOT_FROZEN / NOT_RUN` | Preregistered diagnosis for whether held-out source-class readout degradation reflects fixed-frame degradation, recalibration effects, or recovery under a layerwise readout family. |

## Current Findings

### Supported

- Task-associated discriminative directions are measurable.
- Controlled hidden-state manipulation can produce strong held-out, representation-level target movement.
- EXP-020A replicated this representation-level effect on the same model family at higher parameter scale under frozen controls.

### Negative / failed results remain visible

- EXP-017 did not show task-specific correctness-level behavioral improvement over matched-random control.
- EXP-018 did not pass the relational/invariant preservation gate.
- EXP-019's independent evaluator did not generalize sufficiently.
- EXP-021 Stage-Q fixed source-class readout qualification failed at required downstream clean checkpoints in one complementary split.

### Current Evidence Boundary

Current evidence supports:

- representation-level discriminative structure;
- local representational manipulability;
- same-family higher-parameter representation-level replication.

Current evidence does not yet establish:

- general behavioral control;
- functional binding;
- causal role of the manipulated representation;
- universal task geometry;
- scale invariance;
- a general coordinate transport law.

## Research Navigation

- [RESEARCH-SPINE](docs/research/RESEARCH-SPINE.md) — durable research architecture.
- [CLAIM-LEDGER](docs/research/CLAIM-LEDGER.md) — current claim status.
- [CONSTRUCT-REGISTRY](docs/research/CONSTRUCT-REGISTRY.md) — construct definitions.
- [RESEARCH-CONTINUITY-INDEX](docs/research/RESEARCH-CONTINUITY-INDEX.md) — current research navigation and status.
- [CANONICAL-RESULT-RETENTION](docs/research/CANONICAL-RESULT-RETENTION.md) — evidence durability policy.
- [CURRENT-RESEARCH-HANDOFF](docs/CURRENT-RESEARCH-HANDOFF.md) — current research status snapshot.

For EXP-022A protocol documents, see the [preregistration draft](docs/experiments/EXP-022A-PREREGISTRATION-DRAFT.md), [independent review](docs/experiments/EXP-022A-PREREGISTRATION-REVIEW-092C.md), [rereview](docs/experiments/EXP-022A-PREREGISTRATION-REREVIEW-092E.md), and [protocol reconciliation](docs/research/experiments/EXP-022A-PROTOCOL-RECONCILIATION.md).

## Canonical Evidence

Canonical scientific evidence is retained according to the repository's canonical-result retention policy. See `docs/research/CANONICAL-RESULT-RETENTION.md` for artifact classes and durability rules.

## Current Next Step

EXP-022A is ready to freeze but has not been frozen, run, or formally authorized for implementation. This README synchronization does not authorize model or EVAL execution.

## Repository Checks

```bash
python -m compileall src experiments
python -m pytest tests
```
