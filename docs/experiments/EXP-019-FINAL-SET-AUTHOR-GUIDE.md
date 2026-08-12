# EXP-019 Final-Set Author Guide

This guide prepares human collection of the independent final set. Do not
write examples directly into the repository from this guide. Use the
collection packet and record provenance for every candidate.

## Authorship boundary

Human authors must write `human_authored` responses independently, without
seeing the procedural corpus, classifier predictions, EXP-017 outputs, or
steering conditions. AI-generated text must not be labeled human-authored.

For `manually_adapted_external`, begin with an independent educational or
example source, preserve only the underlying idea, rewrite it concisely, and
record the source family and reference. Do not copy long source text. No
single external source family may exceed 20 of the 100 adapted items.

Codex may create forms, validate structure, count records, detect duplicates,
and flag protocol violations. Codex may not author primary responses, fill
human audit judgments, or fabricate external provenance.

## Response guidance

Responses should be plausible short human answers, grammatically natural,
self-contained, and identifiable from output alone. Use neutral topics across
multiple domains; do not assign one domain to one class.

- **Logic:** express a logical conclusion, entailment, contradiction, or
  condition-based reasoning.
- **Causality:** express a cause-effect or mechanism relationship.
- **Analogy:** express a relation mapping or correspondence.
- **Definition:** express what a concept means, is, or refers to.

Avoid fixed templates and repeated class-marker wording. Do not deliberately
stuff in `holds`, `rule`, `entails`, `mechanism`, `through`, `leads`,
`relation`, `corresponds`, `connect`, `is`, `object`, or `role`.
Avoid bare `Yes.`, `No.`, `Correct.`, isolated nouns, and prompt-dependent
fragments when the task family cannot be recovered from the response alone.

## Length and review fields

Use the frozen bands: short 1–5 tokens, medium 6–12 tokens, and limited-long
13–20 tokens. The target per class is approximately 15 short, 20 medium, and
15 limited-long items. Record self-contained, naturalness, label quality, and
lexical-giveaway judgments only after an actual human review. Only `clear`
items can enter the primary final set.
