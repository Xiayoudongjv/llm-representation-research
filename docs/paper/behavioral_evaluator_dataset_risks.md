# Behavioral Evaluator Dataset Risks

## Primary Risk: Topic Shortcut Learning

An output-only four-class evaluator can learn content vocabulary rather than
task-family response structure. A corpus collected independently per class
would make this risk especially acute: a topic associated mainly with one class
could yield high apparent accuracy without measuring targetness.

## Protocol Response

EXP-019 uses content families to place shared or closely matched concepts across
logic, causality, analogy, and definition responses. It also freezes family-
level splitting, length and format balancing, provenance diversity, lexical and
paraphrase challenges, and duplicate/near-duplicate guards. These controls
reduce shortcut risk; they do not prove that it is eliminated.

## Short-Answer Risk

The EXP-017 outputs are concise. A 1–5-token response may contain insufficient
information for output-only task classification, even with a well-controlled
training corpus. Future work must report performance separately by frozen
length band. Poor short-band performance means targetness is unresolved for
that output regime, not that a convenient longer generation setting should be
introduced post hoc.

## Data and Label Risks

Single-source construction can accidentally encode template, provenance, or
style as a class label. Ambiguous examples can also inflate apparent signal if
they are forced into a category. The protocol requires multiple provenance
categories, no class-unique source domination, independently assigned clear /
borderline / exclude labels, and a blinded human audit of at least 10% of the
eventual dataset.

## Interpretation Risk

Even an accepted classifier measures operational output targetness, not task
competence, reasoning, or successful task conversion. Applying it to EXP-017
is permitted only after its data, training pipeline, test, leakage audit, and
acceptance decision are frozen independently of intervention outputs.
