# Paper A continuous-magnitude audit

The categorical profile labels are retained, but they are not treated as
effect magnitudes. Table 1 and the Figure 2 profile data retain the canonical
continuous statistic and canonical bootstrap confidence interval for every
tested model and every displayed profile axis.

| Model | Distance support (statistic; 95% CI) | SDI class (statistic; 95% CI) | Restricted LOW-D recovery (class; mean; 95% CI) |
|---|---|---|---|
| Qwen3-1.7B | POSITIVE_SUPPORTED; 0.7049462571528698; [0.6851830380886905, 0.7080622074980855] | TARGET_DOMINANT; -0.17355352410373298; [-0.18868527431441903, -0.15827487462584097] | NOT_SUPPORTED; 0.00013923267534205524; [-0.00009933156284070251, 0.00036107659009100833] |
| OLMo-2-1B | POSITIVE_SUPPORTED; 0.7519250367843754; [0.7438987161061725, 0.7582397801058931] | SOURCE_DOMINANT; 0.5249651786448143; [0.49101491890702714, 0.5584696075004959] | SUPPORTED; 0.04785714308465166; [0.044028989621438086, 0.0515186088984566] |
| Meta-Llama-3.2-1B-Instruct | POSITIVE_SUPPORTED; 0.6077483252598234; [0.5949008758383216, 0.6154160155280691] | TARGET_DOMINANT; -0.41426422986393563; [-0.4342173411679606, -0.39239628027572504] | SUPPORTED; 0.0014030612453970375; [0.0007325690004461426, 0.002186791592619705] |

All values above are transcribed from frozen Paper A assets; no statistic was
recomputed for this audit. Support classifications reflect registered
decision rules and should not be interpreted as implying equal effect
magnitudes across models. In particular, the shared `SUPPORTED` LOW-D label
for OLMo and Llama does not collapse their distinct continuous recovery
estimates.

## Interpretation ceiling

The primary construct is **fixed-readout operational compatibility**. The
carrier is the post-block, pre-final-normalization, last-valid-token carrier.
The measurements do not establish semantic equivalence, information
equivalence, geometric equivalence, causal computation, or whole-
representation equivalence.
