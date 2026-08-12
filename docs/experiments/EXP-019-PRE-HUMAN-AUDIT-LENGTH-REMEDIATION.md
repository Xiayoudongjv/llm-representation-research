# EXP-019 Pre-Human-Audit Length Remediation

The pre-human-audit candidate pool contained 11 retained rows above the
frozen 1–20 token policy. They were resolved before the 40-row human audit so
that the reviewer would not be asked to judge known mechanical violations.

## Method

Compression received only `candidate_id` and `response_text`; task class,
classifier output, EXP-017 metadata, and steering conditions were not passed
to the compression function. The edits remove redundant wording only. They do
not add facts, change polarity, alter causal direction, alter an analogy, or
change a defining property.

All 11 rows were classified as `SAFE_SURFACE_COMPRESSION`. No row was marked
`SUBSTANTIVE_CHANGE_REQUIRED`, and no replacement candidate was generated.

## Updated audit and lock

The pre-audit derivative contains 200 rows with 50 per class and all response
lengths within 1–20 tokens. Exact and normalized duplicates, repeated
three-word prefixes, and character TF-IDF similarities were recomputed. The
40-row human sample retained the same candidate IDs and received updated
response text only; all human fields remain blank.

`final200_pre_human_audit_locked.csv` is the sole input for the upcoming human
audit. It is not `final200_frozen.csv`; the freeze gate remains pending until
human judgments are complete.

No evaluator results or EXP-017 outputs were used.
