# Hypothesis Backlog

These entries distinguish questions from evidence. They do not authorize an
experiment and must not be cited as established findings.

## H-001 — Observable/Steerable vs Behaviorally Binding

### Motivation
EXP-018 independently validated a target-directed representation transition,
while EXP-017 did not show stable task-specific correctness-level specificity.

### Existing Evidence
The tested directions were readable and steerable under EXP-018 controls; the
frozen EXP-017 outcome did not favor TASK over matched random overall.

### Unsupported Leap
It is not established that readable or steerable representations are generally
weakly behaviorally binding across LLMs, tasks, layers, or interventions.

### Alternative Explanations
The behavioral measure, intervention timing, strength, task set, generation
dynamics, or single-model design could mask a real but narrower effect.

### Possible Discriminating Test
Use a separately validated target-sensitive behavioral measure and frozen
TASK/random/opposite controls after representation replication.

### Status
CONDITIONAL

## H-002 — Local Open-Loop Intervention vs Global Dynamics

### Motivation
A one-layer perturbation changed a local hidden state, while generation was
produced by continued multi-layer autoregressive computation.

### Existing Evidence
The local transition and generation-time behavioral pilot had different
operational outcomes.

### Unsupported Leap
Current experiments do not show that global dynamics caused the behavioral
failure or that local control is intrinsically insufficient.

### Alternative Explanations
Measurement invalidity, direction misspecification, intervention timing, or
task mismatch could explain the same pattern.

### Possible Discriminating Test
Measure preregistered downstream trajectories after a single intervention,
with baseline, TASK, matched-random, and opposite controls.

### Status
BACKLOG

## H-003 — Downstream Persistence / Attenuation / Reversal

### Motivation
The fate of the target-associated effect after the intervention layer is not
known.

### Existing Evidence
EXP-018 validates movement at selected measurement locations, not persistence
through later layers.

### Unsupported Leap
No evidence currently supports compensation, overwrite, persistence,
attenuation, disappearance, or reversal as a general mechanism.

### Alternative Explanations
Apparent trajectories could depend on probe transfer validity, normalization,
layer semantics, transition pair, or generic perturbation.

### Possible Discriminating Test
Track TASK, matched-random, opposite, and baseline effects at frozen downstream
checkpoints and report heterogeneous transition-level traces.

### Status
PILOT-CANDIDATE

## H-004 — Geometric Separability vs Functional Separability

### Motivation
Historical experiments observed task-associated geometry, but behavioral
specificity was not established.

### Existing Evidence
Representations are geometrically distinguishable in the controlled setup and
can be shifted in a probe-supported direction.

### Unsupported Leap
This does not demonstrate functionally independent computational subspaces or
true latent partitions.

### Alternative Explanations
Lexical, formatting, final-token, or distributed mixed-feature structure could
produce separability without functional modularity.

### Possible Discriminating Test
Use causal interventions and independently valid functional outcomes while
controlling for generic perturbation and surface features.

### Status
BACKLOG

## H-005 — Task Identity as Overlapping Functional Dimensions

### Motivation
EXP-019 generalized unevenly across the four labels, with weak logic and
causality recall and stronger analogy recall.

### Existing Evidence
The frozen classifier failed independent generalization; its per-class errors
are descriptive.

### Unsupported Leap
Classifier failure alone cannot prove that the labels are overlapping latent
dimensions or are not mutually exclusive constructs.

### Alternative Explanations
Dataset composition, wording, feature choice, source variation, or limited
classifier capacity could drive the asymmetry.

### Possible Discriminating Test
Design a separate construct-validity study using multi-label or continuous
dimensions and a new untouched confirmatory set. Do not start it now.

### Status
BACKLOG

## H-006 — Internal vs Operational Invariants

### Motivation
The project used both latent relational metrics and engineering rules that
enforce reproducibility and safety.

### Existing Evidence
Task-specific latent RSM/IVS preservation was not validated. Validators,
hashes, frozen configs, and environment checks do enforce operational rules.

### Unsupported Leap
Operational invariants are not evidence for internal geometric or semantic
invariants.

### Alternative Explanations
High RSM correlation may reflect generic translation properties rather than
task-specific preserved structure.

### Possible Discriminating Test
Develop task-relevant relational controls that outperform matched generic
transformations under held-out validation.

### Status
BACKLOG

## H-007 — Harness as Trajectory Shaping

### Motivation
Agent harnesses repeatedly alter context, action selection, tool feedback, and
environment state rather than directly editing one latent vector.

### Existing Evidence
No current experiment tests a harness. The idea follows from systems-level
control structure, not from project outcomes.

### Unsupported Leap
Do not claim “Harness = Geometry Operator” or conflate generic agent-harness
engineering with a commercial product named Harness.

### Alternative Explanations
Any harness benefit could come from prompting, retries, external computation,
tool access, or selection rather than trajectory control as such.

### Possible Discriminating Test
Hold tools and task fixed while comparing preregistered feedback policies and
recording both text and environment-state outcomes.

### Status
BACKLOG

## H-008 — Closed-Loop Control and the Representation-Behavior Gap

### Motivation
An isolated open-loop intervention may not remain useful throughout generation;
external feedback could repeatedly correct the trajectory.

### Existing Evidence
Current experiments do not test closed-loop feedback or its interaction with
steering.

### Unsupported Leap
There is no evidence that a harness makes representation steering behaviorally
usable or task-specific.

### Alternative Explanations
Closed-loop systems may improve outcomes generically, independently of TASK
direction, or may amplify artifacts.

### Possible Discriminating Test
A future 2×2 pilot could cross Harness OFF/ON with TASK/MATCHED_RANDOM; the
primary question would be the interaction and specificity, not generic
accuracy improvement. Do not activate it now.

### Status
BACKLOG

## H-009 — Agent-Level Outcome vs Text-Only Behavior

### Motivation
EXP-019 showed that an output-only text classifier was not independently valid
for the intended targetness construct.

### Existing Evidence
That measurement failed generalization; no agent-level outcome was tested.

### Unsupported Leap
It is not established that environment-state success is superior for every
task, nor does this reinterpret EXP-017 or EXP-019.

### Alternative Explanations
A better text measure, human annotation, task-specific executable checks, or a
hybrid outcome could be more construct-valid.

### Possible Discriminating Test
For a new tool-using benchmark, preregister environment-state success and
compare it with independently validated text measures.

### Status
BACKLOG
