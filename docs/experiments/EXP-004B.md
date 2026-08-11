# EXP-004B Calibrated Static Steering

## Research Question

Does calibrated static centroid steering cause stronger representation-level
movement when the perturbation is scaled by the actual centroid-difference
magnitude?

## Hypothesis

Using the raw target-minus-source centroid delta should make beta = 1 move a
source centroid approximately toward the target centroid, producing a clearer
change in target similarity and centroid assignment than normalized steering
with small alpha values.

## Why EXP-004B is Needed

EXP-004 showed a monotonic but weak target-similarity increase while target
assignment remained zero. The normalized vector and alpha range may have been
too small relative to the hidden representation scale. EXP-004B calibrates the
perturbation using the actual centroid-difference magnitude.

## Method

Extract last-token representations at layer 16, compute source and target
centroids, and set `delta = target_centroid - source_centroid`. For source-group
representations only, apply `h_beta = h + beta * delta` across a range of beta
values. Evaluate centroid similarities, nearest-centroid labels, and relative
perturbation size.

## Metrics

- Mean similarity to source centroid
- Mean similarity to target centroid
- Target-minus-source similarity
- Target assignment rate
- Mean perturbation norm
- Mean relative perturbation norm

## Expected Outcomes

### Outcome A

Target similarity and target assignment increase more clearly with beta.

Interpretation: calibration reveals stronger representation-level movement
toward the target region.

### Outcome B

Movement remains weak or assignments remain unchanged.

Interpretation: centroid-difference steering may not capture a robust transition
direction even after scale calibration.

### Outcome C

Large beta values produce strong movement but unstable or implausible geometry.

Interpretation: scale calibration may expose an out-of-distribution regime.

## Limitations

- Representation-level steering only.
- No generation-time behavioral evaluation.
- Large beta may create out-of-distribution representations.
- Nearest-centroid reassignment does not prove a reasoning transformation.
- The prompt set and centroid method are small and simple.

## Results

Placeholder: record calibrated steering metrics after running the experiment.

## Next Step

EXP-005 should compare calibrated steering across multiple source-target pairs
or learn a task-conditioned transformation.
