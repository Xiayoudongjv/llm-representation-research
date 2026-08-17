# Research Spine

## Primary scientific chain

Identify -> Manipulate -> Transport -> Preserve -> Bind -> Realize

## Transport decomposition

The simplest member of the transformation/transport ladder may be constrained
calibration:

```text
Identity
-> featurewise recalibration
-> orthogonal
-> affine
-> low-rank
-> nonlinear
```

### A. Clean-state / coordinate transport

```text
h_l^clean -> h_(l+1)^clean
```

### B. Intervention perturbation transport

```text
Delta h_l^tau = h_l^(TASK,tau) - h_l^BASE
```

## Frozen distinctions

- `STATE TRANSPORT != PERTURBATION TRANSPORT`
- `measurement invariance != representation invariance`
- `representation invariance != functional binding`
- `local representational manipulability != causal functional role`

## Scope

This file defines the durable research architecture only. Claim status lives in
`CLAIM-LEDGER.md`. Construct definitions live in `CONSTRUCT-REGISTRY.md`.
Experiment-specific reconciliation lives in
`experiments/EXP-022A-PROTOCOL-RECONCILIATION.md`.
