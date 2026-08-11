# Consolidated Limitations

The evidence in this project is exploratory and representation-level.
All completed experiments use one model, `Qwen/Qwen3-1.7B`, a small manually controlled English prompt set, and last-token hidden-state representations.
The prompt groups are not a broad benchmark of reasoning abilities, and manual prompt design can retain lexical, template, and distributional confounds despite paraphrase controls.

Centroid steering is evaluated without generation-time activation intervention, generated answers, or answer-correctness measurements.
Nearest-centroid assignment measures movement in a chosen representation geometry; it does not demonstrate reasoning transformation or behavioral control.
The RSM-based invariant violation score is a proxy based on six source prompts per group.
It does not prove logical, semantic, or relational invariance, and it may be insensitive to some distortions.
Large calibrated perturbations may create out-of-distribution representations even when the measured proxy appears preserved.
