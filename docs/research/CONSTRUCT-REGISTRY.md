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

## Scope

This file defines constructs only. It does not assign claim status or freeze an
EXP-022A protocol.
