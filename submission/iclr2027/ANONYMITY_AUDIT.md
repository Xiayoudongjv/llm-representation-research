# Anonymity audit

Scope: `paper/`, `appendix/`, `anonymous_artifact/`, copied figure metadata, bibliography, and generated-PDF metadata when a LaTeX toolchain is available.

## Controls

- The official ICLR 2027 anonymous style is used with `iclrfinalcopy` disabled.
- Author and affiliation fields are absent; the style renders the required anonymous-review notice.
- No local filesystem paths, usernames, email addresses, repository URLs, commit history, or private metadata are included in the submission content.
- Cited works and their public author names are bibliography content, not author-identity leaks.
- No model weights, hidden tensors, prompts, source-card content, transcripts, or unrelated experiment notes are included.
- The artifact contains only sanitized machine-readable outputs, hashes, and configuration descriptions.

## Required scan

Run a package-local scan for absolute Windows paths, user directories, email-like strings, repository-host URLs, nonempty author identity fields, and unapproved author names. Inspect PDF metadata after compilation. Any identity leak is a release blocker.

## Status

Static package scan: `PASS` for the populated source/artifact scope. PDF metadata scan remains pending an external LaTeX build because no compiler is installed locally.

No scientific content is changed by this audit.
