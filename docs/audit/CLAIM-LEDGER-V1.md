# Claim Ledger v1

This ledger states the maximum support warranted by the current record after
the construction–evaluation independence audit. “Independent” means that an
outcome is not evaluated using the same fitted centroids, direction, selected
threshold, or aggregate data that constructed the claim.

| ID | Claim | Primary evidence | Independence | Status | Maximum defensible statement |
|---|---|---|---|---|---|
| C01 | Qwen representations show controlled task-group geometry. | EXP-003: L16 separation .073015, silhouette .182165, retention .036424 on 24 prompts. | Descriptive same sample | partially_supported | This designed 24-prompt set has layer-dependent cosine geometry. |
| C02 | Qwen geometry is non-monotonic across depth. | EXP-002/003 sampled layer curves. | Descriptive same sample | partially_supported | The sampled Qwen layers are non-monotonic for these metrics and prompts. |
| C03 | Geometry peaks at a common mid-depth across models. | Qwen L16 versus Gemma EXP-013 separation/retention L26; Gemma silhouette L16. | Same prompt design, second model | contradicted | Peak location is metric- and model-dependent. |
| C04 | Controlled geometry replicates in Gemma. | EXP-013: positive signals, best separation .093294 and retention .071401. | New model, same prompt design | partially_supported | A related descriptive geometry signal occurs in Gemma. |
| C05 | A centroid vector causes a task transition. | EXP-004B/005/006/014 assignment curves. | Fully in sample | operational_only | Adding target-minus-source centroid vectors changes same-sample nearest-centroid labels. |
| C06 | Multi-pair steering validates transition success. | EXP-005/014: 12/12 pairs eventually assignment 1.0. | Fully in sample | operational_only | The same constructed operation works across all ordered group pairs under its own classifier. |
| C07 | Beta .75 is a valid general operating point. | EXP-007: Qwen mean assignment 1, IVS .002850, RSM .997150. | Reuses EXP-006 rows | unsupported | It is an exploratory Qwen operating point for that grid and metric. |
| C08 | Low IVS establishes relational preservation. | EXP-006/014 RSM Pearson/IVS. | No held-out or random-direction comparator | unsupported | IVS is a cosine-RSM correlation proxy under common translation. |
| C09 | Increasing beta trades assignment against preservation. | EXP-006/014 aggregate curves. | In-sample common-translation metrics | partially_supported | These constructed metrics move in opposite directions on the sampled data. |
| C10 | Constraint scans demonstrate robust steering selection. | EXP-008 23/24 lambda/gamma settings select .75. | Same EXP-006 data | operational_only | The discrete winner is insensitive to most scanned scalar weights. |
| C11 | Encoding, control, and safe-control are functional layer roles. | EXP-015/016 fixed sampled grids. | Same-grid extrema and threshold selection | operational_only | They are operational labels defined by the specified rules. |
| C12 | Cross-model role separation is supported. | EXP-016: Qwen control .571 depth, Gemma .615; other roles differ. | Coupled in-sample selection per model | partially_supported | Operational selections differ within models; functional separation is not established. |
| C13 | Safe-control is safe. | EXP-016 Qwen L4@1 has mean assignment .917, IVS .000838, minimum pair assignment .667. | Mean aggregate, in sample | unsupported | It is mean-constrained low-IVS, not pairwise-robust or behaviorally safe. |
| C14 | Representation metrics explain behavior. | EXP-010, EXP-012; n=4, sign changes after frozen benchmark replacement. | No held-out prediction | contradicted | Present group-level associations are benchmark-sensitive and descriptive only. |
| C15 | EXP-011D is an audited behavioral baseline. | 60/80 .750; group accuracies .950/.850/.750/.450. | Behavioral benchmark, no steering | partially_supported | It is a frozen finite-answer baseline with explicit scoring limits. |
| C16 | Steering changes reasoning behavior. | No completed generation intervention. | No evidence | unknown | No claim is supported. |
| C17 | EXP-017 is ready to test behavior causally. | Frozen conditions, random controls, hook specification. | Design only | partially_supported | It is ready for a hook-semantics diagnostic; behavior interpretation remains gated by independence concerns. |

## Claim-language replacements

| Avoid | Use instead |
|---|---|
| task transformation | centroid-directed, in-sample nearest-centroid movement |
| relational invariant | cosine-RSM correlation proxy |
| valid/safe control | mean-constrained, threshold-eligible low-IVS operating point |
| functional layer role | sampled-grid operational role |
| cross-model replication | two-model descriptive replication with model-dependent peaks |
| behavioral relevance | unestablished; current evidence is n=4 and benchmark-sensitive |

## Audit gate

No claim above `operational_only` may be upgraded without evaluation that is
independent of direction fitting and operating-point selection. In particular,
a useful test must separate centroid/direction fitting from evaluation and
compare the real direction to matched-norm alternatives under the same frozen
outcome. This is an evidentiary requirement, not a redesign of any historical
experiment.
