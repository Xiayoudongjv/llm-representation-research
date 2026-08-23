# Paper-A Manuscript Staleness Map

Status: `PA_NOVELTY_002_MANUSCRIPT_STALENESS_MAP`
Manuscript audited: `docs/paper/PAPER-A-FIRST-FULL-DRAFT.md`
Current manuscript coverage: through EXP-025 only.
Required scientific coverage: through EXP-027, with EXP-028 excluded.

## Section Statuses

| Manuscript section | Current state | Required action | Primary flags |
| --- | --- | --- | --- |
| Title | Reflects pre-audit story; emphasizes fixed readout/featurewise recalibration chain | `NEEDS_NOVELTY_REFRAMING` | Remove first-discovery implication; lead with multidimensional compatibility profile |
| Abstract | Contains EXP-025 only; prior-art-aware but still broad | `NEEDS_EXP026_UPDATE`, `NEEDS_EXP027_UPDATE` | Add three-model profiles; add SemRF caution; narrow one-sentence result |
| 1. Introduction | Four prior-art-aware contributions; not yet the narrowed dissociation | `NEEDS_NOVELTY_REFRAMING` | Replace contributions 1-4 with one primary + two secondary; add EXP-026/027 |
| 2. Related Work | Cites Tuned Lens/stitching/functional caution; missing SemRF/HOT/Chen 2025/depth work | `PRIOR_ART_COLLISION`, `REMOVE_OR_REWRITE` | Add SemRF, Chen 2025, Shah 2026, Gupta/Csordas/Curth; reposition as prior art |
| 3.1 Model/checkpoints | Qwen and OLMo only; missing Llama | `NEEDS_EXP027_UPDATE` | Add Llama carrier/final-norm provenance |
| 3.2 Operational semantic class | likely still valid for inherited panel | `STILL_VALID` | Preserve inherited class semantics |
| 3.3 Fixed reference readout | valid | `STILL_VALID` | Preserve fixed readout and split rules |
| 3.4 Featurewise recalibration | valid as operational method | `STILL_VALID` | Preserve T1/T2/conditions |
| 3.5 EXP-024 condition-level design | valid historical evidence | `STILL_VALID` | Keep as negative/panel evidence, not central novelty |
| 3.6 Primary inference | valid | `STILL_VALID` | Preserve registered tests |
| 3.7 Evidence summary | stops at EXP-025 | `NEEDS_EXP026_UPDATE`, `NEEDS_EXP027_UPDATE` | Add profile metrics and routing |
| 4.1 Local manipulability | early ancestry | `STILL_VALID`, `NEEDS_NOVELTY_REFRAMING` | Use only as motivation |
| 4.2 Behavioral boundary | early ancestry | `STILL_VALID`, `NEEDS_NOVELTY_REFRAMING` | Use only as motivation |
| 4.3 Fixed readout degradation | valid but prior art | `PRIOR_ART_COLLISION` | Reframe as background, not novel |
| 4.4 Recalibration recovery | valid but prior-art adjacent | `PRIOR_ART_COLLISION` | Reframe as operational dimension |
| 4.5 Susceptibility negative | valid negative evidence | `STILL_VALID` | Keep as mechanism gap, not primary |
| 4.6 EXP-025 cross-model | valid but only two models | `NEEDS_EXP026_UPDATE`, `NEEDS_NOVELTY_REFRAMING` | Merge with EXP-026/027 profile story |
| 4.7 Integrated synthesis | stops at EXP-025 | `NEEDS_EXP026_UPDATE`, `NEEDS_EXP027_UPDATE` | Replace with three-model profile dissociation |
| 5.1 Observation | valid | `STILL_VALID` | Reframe around profile |
| 5.2 Operational interpretation | valid | `STILL_VALID` | Keep measurement-frame caution |
| 5.3 Negative mechanism result | valid | `STILL_VALID` | Keep mechanism gap |
| 5.4 Open mechanism | valid | `STILL_VALID` | Explicitly not resolved |
| 5.5 Theoretical boundaries | valid | `STILL_VALID` | Keep no-transport/no-binding guardrails |
| 5.6 Measurement resolution | valid | `STILL_VALID` | Keep |
| 6. Limitations | only Qwen/OLMo and two-model scope | `NEEDS_EXP027_UPDATE` | Add three-model limitations; no generalization |
| 7. Conclusion | pre-audit broader claim | `NEEDS_NOVELTY_REFRAMING` | State narrowed dissociation conclusion |
| References | 11 entries; missing audit-critical works | `PRIOR_ART_COLLISION` | Add SemRF, Chen 2025, Shah 2026, Gupta, Csordas, Curth, Tikhomirova, Balogh |
| Figure/Table notes | six figures/two tables pre-EXP026 | `NEEDS_EXP026_UPDATE`, `NEEDS_EXP027_UPDATE` | Add three-model profile figure/table |

## High-Priority Staleness

- Manuscript stops at EXP-025 and lacks EXP-026/027.
- It describes only two models; Llama is absent.
- It still uses the old Qwen-vs-OLMo binary framing.
- It overemphasizes fixed-readout degradation as a primary contribution.
- It lacks SemRF, the strongest current collision.

## Paper-A Manuscript Modification Firewall

- `PAPER_A_MANUSCRIPT_MODIFIED = false`
- No manuscript text, figures, tables, captions, or `references.bib` were changed in this task.
