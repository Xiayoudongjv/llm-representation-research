# EXP-019 AI-Assistance Protocol

## Purpose

Reduce manual source-collection workload while preserving the independence of
the 200-example natural final evaluation set. The existing 760-row corpus
remains a procedural development corpus.

## Allowed AI Assistance

AI may retrieve an approved source, extract compact facts or relations,
organize metadata, count tokens, detect duplicates, flag marker concentration,
and review grammar in a response already written by a human.

## Forbidden AI Assistance

AI may not author final primary `response_text`, generate final external
responses, rewrite a human response into substantively new wording, use
classifier predictions or EXP-017 outputs, fabricate citations, or determine
final inclusion independently.

## Source Whitelist

Preferred sources are Britannica, Khan Academy, OpenStax, NASA, NOAA,
NIH/NCBI educational pages, USGS, Smithsonian educational resources,
university educational pages, Cambridge Dictionary, and Merriam-Webster.
Wikipedia is permitted as a secondary general reference. Reddit, Quora,
Zhihu, personal blogs, SEO content, AI content farms, anonymous forums,
social media, and marketing pages are not primary sources.

## Source Card Design

Source cards contain source metadata, compact facts or relation pairs,
relation type, candidate concept, and notes. They never contain a final
`response_text` field or a sentence intended for direct dataset insertion.
The source-card template is header-only in this task.

## Human Authorship Boundary

After reviewing a source card, a human writes one candidate in their own
words, records provenance, and decides whether it is suitable. Codex may not
fill the primary response or invent external provenance.

## Grammar-Only Correction

For an explicitly supplied human response, AI may return `PASS`,
`NEEDS_MINOR_FIX`, or `UNCLEAR`, with a minimal edit for grammar, punctuation,
agreement, tense, article use, or word order. A correction may not change
semantic content, class, premises, mechanism, relation, or defining property.

## Semantic Change Guard

If a correction would add or remove a premise, causal mechanism, analogy
relation, defining property, or scientific strength, return
`HUMAN_REWRITE_REQUIRED` and do not rewrite automatically.

## Provenance Recording

Record assistance as `none`, `ai_retrieval_only`,
`ai_retrieval_and_grammar`, or `grammar_only`, preferably in `notes` so the
frozen dataset schema is not changed. Final wording and approval remain human.

## Pilot Workflow

1. AI retrieves one approved source.
2. AI creates a source card only.
3. Human reads the card.
4. Human writes the final response.
5. AI performs grammar-only review.
6. Human accepts or rejects any correction.
7. Human enters the response into the collection packet.
8. Mechanical validation runs.

No classifier prediction is visible during these steps. The pilot target is
five source cards per class, 20 total; no source retrieval is performed here.

## Risks

Retrieval can introduce source-selection bias, copied phrasing, citation
errors, and hidden class imbalance. Grammar assistance can become substantive
rewriting. These risks require source records, human approval, duplicate and
marker audits, and explicit semantic-change checks.

## Claim Boundary

This protocol supports collection infrastructure only. It does not establish
evaluator validity, classifier acceptance, or any behavioral effect. EXP-017
outputs remain locked until the independently frozen evaluator passes its
acceptance criteria.
