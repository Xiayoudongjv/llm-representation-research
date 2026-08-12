# EXP-019 Final-200 Freeze Audit

## Dataset Construction

The frozen candidate derives from the documented 200-row EXP-019 construction workflow. It contains 50 examples each for logic, causality, analogy, and definition, with response lengths from 4 to 20 tokens.

## Alignment Repair

The prior alignment review and correction records remain preserved as historical audit materials.

## Random-40 Human Audit

The completed Random-40 audit recorded 38 `Y`, 2 `N`, and 0 uncertain judgments.

## Logic Spot Check

The ten-item Logic spot-check recorded 9 `Y`, 1 `N`, and 0 uncertain judgments.

## Logic Remediation

Three Logic mismatches were removed and replaced. The three replacement decisions are `Y`; `REMED-LOG-002` was accepted under the existing frozen exclusion/contradiction criterion through the recorded `REVIEW_CRITERION_CLARIFICATION`.

## Similarity Review

The completed compact similarity review had 16 flagged entries: 10 `Y`, 6 `N`, and 0 `?`. One semantic duplicate pair was flagged twice, yielding five unique substantive redundancy problems.

## Similarity Remediation

Five specified redundant rows were removed while their documented counterparts were retained. Five replacement candidates were added without reusing removed concepts.

## Replacement Review

`REMED2-DEF-001`, `REMED2-DEF-002`, `REMED2-CAU-001`, `REMED2-CAU-002`, and `REMED2-LOG-001` each received `Y` in targeted human review.

## Remaining Descriptive Similarity Flags

The final candidate has 7 repeated three-word-prefix groups and 2 character TF-IDF cosine pairs at or above 0.55. Remaining repeated-prefix / TF-IDF similarity flags were not treated as automatic failures because no exact or normalized duplicates remained and human-identified substantive redundancies had already been remediated.

## Freeze Decision

`READY_TO_FREEZE`

The frozen dataset SHA-256 is `48E05DB992185661DF41C102C32CD4685944E50D0CD7454A195AB63C7B638765`.

## Scientific Independence

The evaluator was frozen before Final-200 evaluation. No Final-200 predictions were viewed before dataset freeze. EXP-017 outputs remained unread. The evaluator artifact SHA-256 is `DF06E7683627F308330E77E8A50D35766F3CA50F5C8DE873E077092DEAEB2BDD` and evaluator config SHA-256 is `EB673B63CB0C407C04F55F9B5F8FB687C7BD680FC5B53DDD4CC18A2BCC906744`.

## Next Gate

The next authorized action is the separately governed, one-shot Final-200 evaluator test. This freeze task did not run that evaluation and did not unlock EXP-017.
