# Paper Draft v0.6: Audit-Integrated Evidence Restructuring

*Provisional title: From Representation Shift to Behavioral Control: Auditing
Task-Associated Steering in LLM Hidden States*

## Abstract

We study task-associated hidden-state geometry and centroid-derived steering in
Qwen/Qwen3-1.7B and google/gemma-3-1b-it. The project began with descriptive
controlled geometry and in-sample centroid-transition observations. A research
audit then found that historical nearest-centroid transition metrics were
construction-coupled and that low cosine-RSM disruption was not task-specific
evidence. A held-out cross-paraphrase validation subsequently showed
task-directed representation movement beyond matched-norm random and opposite
controls: the independent probe's target probability increased in 216/216
conditions, with mean TASK-minus-random difference +0.836584. The same study
failed to validate task-specific relational preservation: the IVS advantage was
positive in only 78/216 conditions (36.1%), with median -0.000048. Finally, a
frozen Qwen generation-time pilot found no overall behavioral advantage of the
task vector over equal-norm random perturbation (both .6375 accuracy, versus
.750 baseline). The contribution is therefore an evidence-audited account of
where representation-level steerability survives stronger controls and where it
does not translate to relational or behavioral claims.

## 1. Central Question

What evidence is required to distinguish a genuine task-associated
representation transition from construction-coupled metrics, and does such a
validated representation transition translate into task-specific generation
behavior?

Secondary questions are whether controlled geometry appears across model
families; whether centroid-derived directions yield held-out independently
decodable target movement; whether apparent relational preservation is specific
to task steering; and whether validated representation steering differs from
matched random perturbation during generation.

## 2. Evidence Sequence

The central story is not a monotonic validation narrative:

1. **Observation.** EXP-003 found controlled Qwen task-group geometry on 24
   paraphrase-controlled prompts.
2. **Operational steering.** Earlier centroid steering moved same-sample source
   representations toward target centroids under nearest-centroid metrics.
3. **Audit.** Research Audit v1 identified construction-evaluation coupling and
   the nonspecificity of absolute cosine-RSM preservation.
4. **Independent representation validation.** EXP-018 used disjoint fit/eval
   splits, a frozen linear probe, matched-random, and opposite controls.
5. **Relational failure.** EXP-018 did not validate task-specific RSM/IVS
   preservation.
6. **Behavioral failure.** EXP-017 did not validate task-specific behavioral
   advantage over matched random perturbation.

## 3. Controlled Geometry Across Models

On the fixed 24-prompt design, Qwen's strongest reported controlled signal was
at L16 (separation .073015, silhouette .182165, paraphrase retention .036424).
Gemma showed positive controlled structure across several nonembedding layers;
its highest separation (.093294) and retention (.071401) were at L26, whereas
its highest silhouette (.139718) was at L16. Thus related controlled geometry
appeared in two small model families, but peak depth was metric- and
model-dependent. This is descriptive evidence on a hand-designed prompt set,
not a universal geometry law.

## 4. What the Audit Changed

At beta 1, adding a target-minus-source centroid vector makes the source mean
equal the target centroid. Earlier work then evaluated movement with centroids
fitted on the same representations. That is an operational vector-arithmetic
check, not independent task conversion. Separately, a matched-norm random
common translation can retain high cosine-RSM correlation, so low IVS cannot by
itself demonstrate task-specific relational preservation. These observations
required both an independent evaluator and matched generic perturbation
controls.

## 5. Independent Representation Validation

EXP-018 split original-style and paraphrase prompts into complementary
three-per-group fit/evaluation sets. It fitted centroids and a frozen
multinomial linear probe on fit examples only, then evaluated held-out source
representations under task, deterministic matched-random, and opposite vectors.
Across 216 model/layer/split/transition/beta conditions, TASK increased target
probe probability in 216/216. TASK exceeded matched random in 216/216, with
mean difference +.836584 and median +.879981; it exceeded opposite in 216/216,
with mean +.947121. This supports held-out, probe-supported target-directed
representation movement for the tested small controlled design.

## 6. Decomposing Validity Claims

This paper treats three questions as an evaluation decomposition, not a proven
universal definition of validity.

- **Transition validity:** Does a fixed intervention produce target-directed
  movement under held-out, construction-independent evaluation? EXP-018
  supports this in the tested setting.
- **Preservation validity:** Does it preserve non-target or relational
  properties better than matched generic perturbations? Current RSM evidence
  does not support this.
- **Behavioral validity:** Does it produce target-specific behavior rather than
  generic perturbation effects? EXP-017 does not support this outcome.

For EXP-018, IVS_random minus IVS_task was positive in only 78/216 conditions
(36.1%), with mean +.037607 but median -.000048 and model/split inconsistency.
Thus `relational_validation = FAILED`; RSM/IVS remains a perturbation
diagnostic, not evidence of task-specific relational preservation.

## 7. Operational Layer-Role Results

EXP-015/016 sampled geometry, assignment, and RSM metrics across layers and
strengths. The resulting encoding/control/safe labels are operational
sampled-grid selections. Qwen's encoding/control selection differed from its
mean-constrained safe selection under historical metrics; Gemma's encoding
selection differed from control on the sampled grid. Because RSM validation
failed and no behavioral layer comparison was performed, these are not
functional layer hierarchies or validated safe/validity layers. In particular,
L4 and L28 are not treated as validated behavioral operating points.

## 8. Behavioral Evidence

EXP-011D froze a Qwen baseline at 60/80 (.750): causality .950, definition
.850, logic .750, and analogy .450. EXP-012's four-group descriptive
representation-behavior correlations were benchmark-sensitive, including sign
changes after baseline replacement; it is correlational and not stable.

EXP-017 is a distinct causal pilot. Its deterministic no-intervention condition
exactly reproduced EXP-011D. The independently validated L16 direction,
matched-norm random direction, and opposite direction were applied to the
frozen 80-item benchmark. TASK and RANDOM each achieved .6375 overall
accuracy, while OPPOSITE achieved .6625. TASK minus RANDOM was 0.0000 overall;
the group contrast was mixed (-.15 logic, -.05 causality, -.20 analogy, +.40
definition). The random condition had malformed rate .20 overall and .55 in
definition, contaminating the main group where TASK outperformed random.

The behavioral conclusion is `behavioral_effect = FAILED` and
`representation_behavior_link = NOT_SUPPORTED`. The current source-accuracy
outcome cannot identify target-task conversion; it also does not show a stable
task-specific advantage beyond generic perturbation.

## 9. What Did Not Survive Stronger Controls?

1. A universal mid-depth peak: Gemma's strongest separation/retention was final
   layer L26.
2. A universal beta-.75 frontier: the historical operating point did not
   transfer as a fixed cross-model rule.
3. RSM/IVS as task-specific relational preservation evidence: independent
   task-versus-random comparison failed.
4. Representation transition implying task-specific generation behavior:
   EXP-017 found no overall TASK advantage over RANDOM.
5. Representation metrics explaining behavioral difficulty: EXP-012's
   group-level correlations were benchmark-sensitive at n=4.

These are first-class negative or downgraded results, not hidden limitations.

## 10. Contributions

1. Controlled cross-model analysis of task-associated hidden-state geometry.
2. A calibrated centroid-based representation intervention baseline.
3. An audit showing that nearest-centroid transition metrics and absolute RSM
   preservation can be construction-coupled or nonspecific.
4. A held-out validation protocol with fit/evaluation separation,
   cross-paraphrase splits, a frozen linear probe, and random/opposite controls.
5. Evidence that task-derived representation transitions survive this
   independent validation in two small model families.
6. Negative evidence that the tested RSM proxy does not establish task-specific
   relational preservation.
7. Negative behavioral evidence that representation-level steerability was not
   sufficient for task-specific generation-time control in the frozen Qwen
   pilot.

## 11. Limitations and Conclusion

The record covers two small models, a 24-prompt controlled representation set,
and one 80-item Qwen behavioral benchmark. It uses last-token states and a
centroid-based intervention. The behavioral outcome is source-task accuracy,
not a target-sensitive evaluator. Results do not establish reasoning
improvement, task conversion, safe steering, generalization to larger models,
or a universal theory of representation validity.

The strongest positive result is independently validated target-directed hidden
state movement. The strongest negative result is that this movement did not
yield a stable behavioral advantage over equal-norm random perturbation. The
project's contribution is the distinction, not a new steering algorithm.
