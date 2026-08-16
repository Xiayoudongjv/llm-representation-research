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

## Scope

This file defines constructs only. It does not assign claim status or freeze an
EXP-022A protocol.
