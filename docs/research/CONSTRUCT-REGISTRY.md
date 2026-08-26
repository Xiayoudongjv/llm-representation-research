# Construct Registry

## Representation

```text
h_l(x) = clean or explicitly conditioned hidden representation at layer l
```

## Semantic labels

```text
SOURCE_SEMANTIC_CLASS = intrinsic controlled-item semantic class
TARGET_SEMANTIC_CLASS = destination class of a directed task intervention
```

## Historical intervention

```text
delta_(s->t) = centroid_target_FIT - centroid_source_FIT
```

```text
h' = h + beta * delta_(s->t)
```

This is the EXP-018/EXP-020A operational construction, not a universal theory
of task directions.

## Distinct objects

```text
d_l / S_l = task-associated discriminative structure
delta_l   = injected intervention
Delta h_l = h_l^TASK - h_l^BASE
```

Frozen distinction:

```text
d_l != delta_l != Delta h_l
```

## Measurement instrument

```text
M = representation extraction
    + scaler
    + classifier
    + class mapping
    + FIT provenance
    + EVAL protocol
```

## Readout adaptation levels

- `A0 Fixed Frame`
- `A1 Featurewise-Affine Recalibration`
- `A2 Layer-wise Linear Refit`
- `A3 structured alignment = future / outside EXP-022A primary`
- `A4 nonlinear adaptation = future / outside EXP-022A primary`

## Featurewise recalibration

```text
FIT-only per-feature location/scale adaptation applied before a fixed readout.
```

## Diagonal affine transport

```text
A constrained coordinate transformation acting independently on feature
dimensions.
```

## Representational overlap

```text
Shared/local co-occupancy of representation regions.
```

## Destructive interference

```text
Overlap or transformation interaction that impairs task-relevant readout or
function.
```

## Structured belief representation

```text
Representation that preserves multiple candidate latent/world states and their
uncertainty.
```

## Operator-valued edge

```text
A typed connection that applies a member of a constrained transformation family
to a source state before delivering a message to a destination state.
```

## Structured multi-hypothesis node state

```text
A node state that preserves multiple candidate latent states together with
confidence or belief weights.
```

## Conditional operator selection

```text
A policy that chooses a transformation operator from a vocabulary based on
state, context, task, or uncertainty.
```

## Representation state

```text
The current represented object or configuration, from which future transformations or readouts are computed.
```

## Transformation operator

```text
A reusable mapping from representation states to representation states.
```

## Attention–geometry coupling

```text
The potential reciprocal relation in which representation geometry influences attention routing, and attention-mediated value transport changes downstream representation geometry.
```

## Relational alignment

```text
The attention-score stage that weights relationships between positions.
```

## Attention-mediated value transport

```text
The attention-output stage that aggregates value vectors across token positions.
```

## Representation Flow

```text
h_0 -> h_1 -> ... -> h_L
```

A network trajectory viewed as successive representation states.

## Incremental operator

```text
h_{l+1} = T_l(h_l) = h_l + F_l(h_l) for residual-style systems
```

`F_l` is the layer-local incremental transformation.

## Accumulated Compatibility Distortion

A prospective operational interpretation of `D(i,j)` as a measure of how much
a composed representation transformation disrupts compatibility with a
source-trained fixed readout. `D(i,j)` is not yet a geometric distance,
information-loss, causal-distortion, or transport-cost measure.

## Representation Trajectory Conserved Structure

A prospective invariant along a representation trajectory:
`I(h_{l+1}) ≈ I(h_l)`, or continuous approximation `dI(h(t))/dt ≈ 0`.

No specific invariant has been validated.

## Near-identity deviation from identity

For residual form `T = I + Δ`, future measures may include `||Δ||`,
Jacobian deviation `J_l - I`, operator norm, low-rank update magnitude, and
other prospectively defined complexity measures. No specific norm is frozen.

## Post-Anchor Prospective Construct Reconciliation

The constructs in this section are `UNREGISTERED_PROSPECTIVE_CONSTRUCTS`.
They define vocabulary and future falsification obligations only. They do not
enter the Claim Ledger, alter canonical experiment interpretation, activate an
Innovation Candidate, or establish a new hypothesis.

### Cross-Gap Audit

Before a prospective bridge is promoted, record the intervening links rather
than reasoning directly from `A -> C`. A bridge must identify:

1. what changes;
2. what must remain invariant;
3. the exact or approximate equivalence notion;
4. where any displaced cost goes;
5. whether validity survives composition; and
6. an observation that would falsify the bridge.

The audit routes an item through the existing governance sequence:
`INSPIRATION -> THEORY_CANDIDATE -> HYPOTHESIS_CANDIDATE -> REGISTERED_HYPOTHESIS -> EVIDENCE`.
Only the final two stages can affect an experimental claim, and only through
their existing separate authorities.

### Task-Relative Admissibility and Structural Signature

Prospective framework:

```text
Task semantics -> task-relative invariant -> representation/state
-> structural signature -> typed operator family -> admissible region
-> composition/trajectory -> realization -> binding/execution -> observation
```

For task-relative invariant `I`, a transformation `T` is admissible only under
an independently specified condition such as `Violation_I(T) <= epsilon` and
declared resource/error semantics. This does not define an invariant for any
current experiment.

`Open Structural Degree Principle` is the current form of the historical
`234` intuition. A structural degree tuple may be written
`Omega = (q, d, r, m, n, b, ...)` for state cardinality, representation
dimension, relation order, input arity, output coarity, branching factor, and
other declared degrees. A structural signature may be written
`Sigma = (Omega, typed_choices, constraints)`. Physical binary encoding is not
the same thing as computational state structure, and no degree is presumed
better merely because it is larger.

### Typed Transformations and Representation-Relative Computation

A transformation contract may include type, domain, codomain, reversibility,
preconditions, invariants, side effects, approximation/error semantics, and
cost consequence. Candidate categories include reversible,
irreversible-but-valid, projection/coarse-graining, extension, coupling, and
conditional/non-local transfer.

For invertible change of representation `h`, a primitive can have a
representation-relative realization:

```text
F_h = h o F o h^-1
h o F = F_h o h
```

For non-invertible maps, use an explicitly scoped intertwining or
encoder/decoder relation such as `h o F ~= G o h` or `D o G o E ~= F`.
Log/multiplication-addition and Fourier/convolution-multiplication are mature
mathematical examples, not project novelty or evidence.

`Algorithmic realization equivalence` names the prospective distinction
between recursive, iterative, matrixized, parallel, memoized, cached,
closed-form, representation-changed, tool-assisted, or hardware-specific
realizations of one task. Exact semantic, observational, task-invariant, and
approximate equivalence are distinct and must be defined before use.

### Control and Memory as State Realization

Continuation state may be realized through an implicit or explicit stack,
queue, continuation, continuation graph, task DAG, scheduler frontier,
futures/promises, or work queue. `call_stack = O(1)` never by itself implies
`total_memory = O(1)`.

For semantic state `s`, a memory realization family may contain full resident
state, compression, base-plus-delta, shared immutable state, checkpoint,
recomputation recipe, solved-state reference, or disk/remote realization.
Exact recovery requires `Recover(m_i) = s`; approximate recovery requires an
independently declared `d(Recover(m_i), s) <= epsilon`.

`Memory folding` is any map from one realization to another subject to its
declared recovery/invariant requirement. It is not synonymous with PCA.
`State-overlap quotient` permits sharing only when `s_i ~_I s_j` under a valid
task-relative equivalence relation; similarity alone is not sufficient for
exact merging. A recursive-tree-to-shared-DAG transformation is illustrative,
not a claim of universal sharing validity. `Memory-compute exchange` records
the ordinary tradeoff between storage and recomputation under total cost.

### Local Realization, Sparse Execution, and Minimum Sufficiency

`Local realization polymorphism` denotes the prospective family `R(G_i)` of
valid realizations of computational subgraph `G_i`. A system can choose a
heterogeneous realization vector rather than one global execution style.

`Potential -> admissible -> selected -> executed` distinguishes the large
potential realization space `R_F` from a state/context/resource-conditioned
admissible region and its sparse executed trajectory. It is an architecture
principle, not a complexity theorem.

`Minimal sufficient realization` asks for the minimum declared realization
complexity sufficient to satisfy a required invariant and performance
criterion. Operator, structure, memory, control, and search complexity remain
separate cost terms until a future protocol defines them.

### Composition, Return, Navigation, and Geometry

`Compositional validity` asks when `Valid(T_1)` and `Valid(T_2)` support
`Valid(T_2 o T_1)`. Side effects, aliasing, shared state, concurrency,
resources, approximation, noncommutativity, and task-conditioned validity are
part of the prospective problem rather than ignorable details.

The return hierarchy distinguishes raw-state return (`R0`),
coordinate/alignment-equivalent return (`R1`), structural/invariant return
(`R2`), and functional return (`R3`). No level automatically implies a later
level, and final return does not imply pathwise validity.

`Invariant-constrained geometric navigation` is the prospective question of
selecting `T* = argmin C(T)` subject to declared invariant defect and
admissibility constraints. Optimization methods (Newton/BFGS, proximal,
penalty, ADMM, Krylov/CG) are inspirations for local metrics, constrained
updates, decomposed constraints, and dynamic search subspaces; they are not
literal `234` primitives.

`Geometry selection` permits Euclidean, hyperbolic, spherical, learned-metric,
or Riemannian candidates, with Euclidean geometry retained as a baseline/null
model. Dynamic geometry distinguishes state trajectory `x(t)` from
metric/space evolution `g(t)`. No current experiment establishes dynamic
latent geometry.

### Mathematical Inspiration and Systems Routing

Cross-representation problem solving asks whether a solver should search for a
representation `h` in which a problem is easier, while preserving a declared
solution relation. It is motivated by mature transforms and correspondence
examples, not by a claim that Erdos, Kakeya, Langlands, quantum theory, or
Ramanujan mathematics proves this research program.

`Invariant-constrained operator coverage` is a prospective question about the
smallest operator family whose reach covers a required task region while
respecting declared constraints. Collatz supplies an independent sandbox for
state-dependent operator selection, drift, excursion, return, escape, and
counterexample concepts; it supplies no convergence evidence for LLMs.

The reconciled `Harness` is a prospective system composition:
`candidate generator + admissibility gate + planner + verifier + cost model +
executor + experience/outcome memory`. Project C / GIR remains a narrow
exploratory prototype route (Python subset -> AST -> GIR -> small typed
transformation vocabulary -> legality gate -> correctness/runtime benchmark),
not a claim of novel compilers or a full runtime/OS agenda.

## Scope

This file defines constructs only. It does not assign claim status or freeze an
EXP-022A protocol.
