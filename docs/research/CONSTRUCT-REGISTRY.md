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

## Scope

This file defines constructs only. It does not assign claim status or freeze an
EXP-022A protocol.
