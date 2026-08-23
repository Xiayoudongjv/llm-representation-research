# Paper-A Final Novelty Boundary

Status: `PA_NOVELTY_003_FINAL_NOVELTY_BOUNDARY`
Route: `ROUTE_B_STANDALONE_NARROWED`
Final decision: `STANDALONE_VIABLE_BUT_HIGH_RISK`

## One-Paragraph Boundary

Paper-A may claim only that, in three prospectively registered 1B-class language models, all three show positive depth-distance-associated fixed-readout compatibility structure, while source/target organization and simple LOW-D recalibratability form non-identical combinations. Llama is the crucial third profile: it shares Qwen's target-dominant organization but OLMo's supported LOW-D recovery. This is a modest but real empirical inference; it is not statistical independence, causal independence, architecture causality, training-history causality, a universal taxonomy, or transport evidence.

## Permitted Claims

- Three tested models support positive distance-associated fixed-readout compatibility structure.
- Qwen: `TARGET_DOMINANT + NOT_SUPPORTED`.
- OLMo: `SOURCE_DOMINANT + SUPPORTED`.
- Llama: `TARGET_DOMINANT + SUPPORTED`.
- The Llama profile breaks the simple two-model mapping.
- Within the tested set, SDI and LOW-D are not deterministically equivalent.
- A single scalar depth/degradation score is insufficient for these measured properties.

## Prohibited Claims

- First discovery of fixed-readout incompatibility.
- First source-target matrix.
- Universal compatibility regimes or laws.
- Statistical or causal independence of SDI and LOW-D.
- Architecture or training history causes profile differences.
- Recalibration failure predicts adapter failure.
- Fixed-readout degradation means semantic information disappeared.
- EXP-028, Residual-Flow, invariants, Functional Binding, or transport are supported.
- Results generalize to all LLMs or Transformers.
- Demonstrated practical/industry impact.

## Contribution Hierarchy

- PRIMARY: three-model empirical profile dissociation with prospective third-model evidence.
- SECONDARY: multidimensional operational characterization of cross-depth fixed-readout compatibility.
- SECONDARY: registered three-model profile comparison.
- METHODOLOGICAL: carrier comparability and prospective governance.

## Collision Severities

- SemRF: `MODERATE`
- Tuned Lens: `MODERATE`
- Patchscopes: `MINOR`

## Venue Fit

- TMLR: `PLAUSIBLE`
- ICLR: `BORDERLINE`
- ICML: `BORDERLINE`
- NeurIPS: `BORDERLINE`

## Resume Gate

- `PAPER_A_MANUSCRIPT_RESUME_ALLOWED = true`
- This authorizes future manuscript engineering only.
- No manuscript was modified in this task.

## Final Flags

- `NOVELTY_VERDICT = MODEST_BUT_REAL_NOVELTY`
- `SCIENTIFIC_VALUE = USEFUL_EMPIRICAL_INSIGHT`
- `PAPER_A_EXTENSION_REQUIRED = false`
- `PAPER_A_MANUSCRIPT_MODIFIED = false`
- `NEW_EXPERIMENT_PERFORMED = false`
