# Claims Checklist v0.6

This ledger records the current wording ceiling after Research Audit v1,
EXP-018, and EXP-017. “Supported” is scoped to the stated datasets, models, and
evaluators; it is not a general claim.

| Claim | Status | Current wording ceiling |
|---|---|---|
| Controlled task geometry in Qwen | PARTIALLY_SUPPORTED | The 24-prompt design has layer-dependent controlled cosine geometry in Qwen. |
| Controlled task geometry in Gemma | PARTIALLY_SUPPORTED | A related descriptive controlled geometry signal occurs in Gemma. |
| Cross-model task geometry | PARTIALLY_SUPPORTED | Related geometry appears in two small model families on the same designed prompt set. |
| Universal peak depth | CONTRADICTED / FAILED_VALIDATION | Peak location is metric- and model-dependent. |
| Historical centroid steering | OPERATIONAL_ONLY | Target-minus-source vector addition changes same-sample centroid-related measures. |
| Held-out representation steering | SUPPORTED | The frozen EXP-018 procedure produced held-out target-directed probe movement. |
| Independent task-directed representation transition | SUPPORTED | TASK exceeded matched random and opposite on the frozen independent probe in the tested setup. |
| Universal beta frontier | CONTRADICTED / FAILED_VALIDATION | Historical beta choices are exploratory and model-dependent. |
| RSM relational preservation | CONTRADICTED / FAILED_VALIDATION | The RSM proxy did not show task-specific preservation against matched random. |
| Transition-preservation validity frontier | NOT_SUPPORTED | It is not an empirically validated joint validity formula. |
| Encoding/control/safe layer roles | OPERATIONAL_ONLY | These are sampled-grid definitions, not functional modules or validated safe layers. |
| Representation-behavior correlation | CONTRADICTED / FAILED_VALIDATION | Four-group descriptive links are benchmark-sensitive and nonpredictive. |
| Generation-time task-specific behavior | CONTRADICTED / FAILED_VALIDATION | The frozen Qwen pilot found no stable TASK advantage over matched random. |
| Steering improves reasoning | NOT_SUPPORTED | No reasoning-improvement evidence exists. |
| Target-task conversion | NOT_SUPPORTED | No target-sensitive behavioral measure was used. |
| Opposite direction yields behavioral reversal | NOT_SUPPORTED | Opposite-control behavioral differences were mixed. |
| IVS predicts behavioral safety | NOT_SUPPORTED | Neither independent RSM validation nor behavior supports this. |
| EXP-011D baseline | PARTIALLY_SUPPORTED | It is a frozen finite-answer Qwen baseline with stated scoring limits. |

## Claim-language replacements

| Avoid | Use instead |
|---|---|
| task conversion | held-out target-directed representation movement |
| relational invariant | cosine-RSM correlation proxy |
| safe or validity layer | operational sampled-grid selection under historical metrics |
| functional layer hierarchy | operational layer-role separation |
| behavioral control | not established beyond generic perturbation effects |
