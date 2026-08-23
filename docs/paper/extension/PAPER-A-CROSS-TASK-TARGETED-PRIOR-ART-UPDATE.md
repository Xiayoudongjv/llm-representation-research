# Paper-A Cross-Task Targeted Prior-Art Update

Status: `PA_EXT_A_001_TARGETED_PRIOR_ART_UPDATE`

Decision context: `PA-VALUE-000` selected
`ROUTE_A_FRESH_CROSS_TASK_REPLICATION` as the single authorized Paper-A
extension. This document is the required pre-protocol prior-art update and
does not create a panel, result, authorization, or manuscript change.

## 1. Search Scope

The update targeted the following questions:

- cross-task probe stability
- cross-task readout portability
- task-dependent layerwise probing
- cross-task representation similarity / alignment
- probe transfer across semantic tasks
- layerwise representation stability across tasks
- model x task interaction in probing
- cross-depth measurement stability

The existing Paper-A prior-art assets were reused for the baseline:

- `docs/paper/PAPER-A-NOVELTY-AND-SIMILARITY-AUDIT.md`
- `docs/paper/PAPER-A-PRIOR-ART-GAP-NOTE.md`
- `docs/paper/PAPER-A-PRIOR-ART-OVERLAP-MATRIX.json`

## 2. Existing Baseline, Already Established

The following are already acknowledged and are not claimed as new here:

- Tuned Lens: layer-specific affine probes are often useful or necessary.
- Model stitching / representation stitching: simple adapters can restore
  substantial task performance, but functional recovery is not equivalent to
  representational equivalence.
- Functional-alignment caution: stitching success can occur even when the
  underlying representations differ.
- Layerwise probe-transfer work: readout portability is often limited and
  depth/task sensitive.

Those works establish that fixed readouts and alignment procedures are
known. They do not establish the prospective cross-task stability of a frozen
three-model, three-component compatibility-profile routing system.

## 3. Newly Retrieved Evidence

### 3.1 Task-dependent layerwise state encoding

- Title: *Task Structure Reverses Layerwise State Encoding in Sequence Models*
- arXiv: `2606.00926`

Relevance: shows architecture signatures and layerwise state encoding are
task-dependent. This supports treating task/panel dependence as a live
scientific risk. It does not run the frozen EXP-026/027 fixed-readout matrix
protocol across an independently designed second panel.

### 3.2 Truth-direction limits are layer/task dependent

- Title: *Testing the Limits of Truth Directions in LLMs*
- arXiv: `2604.03754`

Relevance: truth probes are highly layer-dependent and task-sensitive. This
reinforces the need for a second task panel, but is not a cross-task
replication of the Paper-A source/target compatibility and LOW-D recovery
profile.

### 3.3 Probe task-format confound

- Title: *Linear Probes Detect Task Format, Not Reasoning Mode in Language
  Model Hidden States*
- arXiv: `2606.02907`
- Venue: TrustNLP 2026, ACL Anthology `2026.trustnlp-main.12`

Relevance: task format can confound layerwise probing conclusions. This is a
caution for cross-task interpretation, and it strengthens the requirement that
the new panel be genuinely independent and outcome-blind. It does not test the
Paper-A three-model joint profile under task replacement.

## 4. Operation-Level Adjudication

Compare the proposed scientific operation, not terminology:

A. Cross-task stability of fixed-readout compatibility matrices:
   `NOT_ESTABLISHED_BY_RETRIEVED_PRIOR_ART`

B. Cross-task stability of source/target organizational summaries:
   `NOT_ESTABLISHED_BY_RETRIEVED_PRIOR_ART`

C. Cross-task stability of simple recalibratability:
   `PARTIAL_ADJACENT_EVIDENCE_ONLY`

D. Cross-task stability of the JOINT model-level profile:
   `NOT_ESTABLISHED_BY_RETRIEVED_PRIOR_ART`

E. Prospectively tested model x task profile interaction:
   `NOT_ESTABLISHED_BY_RETRIEVED_PRIOR_ART`

## 5. Adjudication

`PRIOR_ART_ROUTE = PARTIALLY_OVERLAPPING_BUT_DISTINCT`

The adjacent literature overlaps in motivation and in individual measurement
components, especially layerwise probing, task dependence, and readout
portability. It does not subsume the proposed operation: replacing only the
semantic task panel while holding three model identities, carrier semantics,
depth coordinates, fixed-readout procedures, statistics, and routing fixed.

Therefore protocol design may proceed.

## 6. Hard Flags

- `TARGETED_PRIOR_ART_UPDATE = PASS`
- `PRIOR_ART_ROUTE = PARTIALLY_OVERLAPPING_BUT_DISTINCT`
- `PRIOR_ART_SUBSUMED = false`
- `NEW_PANEL_CREATED = false`
- `PAPER_A_MANUSCRIPT_MODIFIED = false`