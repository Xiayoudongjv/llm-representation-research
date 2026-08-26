# ICLR 2027 anonymous submission package

This directory contains the anonymous Paper A submission package prepared with the official ICLR 2027 style files. The package is a presentation and reproducibility boundary only; it does not alter canonical experiment results, claim registers, or scientific authorities.

## Contents

- `paper/main.tex`: anonymous main paper source.
- `appendix/appendix.tex`: appendix included after the bibliography.
- `paper/references.bib`: verified bibliography used by the paper.
- `anonymous_artifact/`: minimal result/configuration artifacts and validation metadata; no model weights, hidden tensors, prompts, or repository history.
- `ANONYMITY_AUDIT.md`, `PAGE_BUDGET.md`, and `AI_USE_AUDIT.md`: package checks and author-facing records.
- `PRIVATE_AUTHOR_CHECKLIST.md`: not for upload.

## Official template

The package uses the ICLR 2027 style files downloaded from the official conference style archive on 2026-08-26. The source archive is retained outside the anonymous artifact for provenance. The submission is compiled with `iclr2027_conference.sty` and `iclr2027_conference.bst`; `iclrfinalcopy` remains disabled.

Official sources: https://iclr.cc/Conferences/2027/AuthorGuidelines and https://iclr.cc/Conferences/2027/AIPolicyForAuthors.

## Build

From `paper/`, a standard LaTeX toolchain can build the single paper-plus-appendix PDF:

```text
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

The bibliography is placed before `\appendix`, so references are excluded from the main-text page count and the appendix follows the bibliography. The local Windows environment used to prepare this package did not contain `pdflatex`, `bibtex`, `latexmk`, or `tectonic`; therefore PDF compilation and visual page inspection remain an external-toolchain check.

Ethics disposition: `ETHICS_STATEMENT_REQUIRED=false`. The project has no material ethics issue requiring a paper section beyond ordinary research-integrity, reproducibility, and anonymity checks; no ceremonial ethics section is included.

## Upload boundary

Upload `paper/main.tex`, `appendix/appendix.tex`, the required local style/bibliography/figure files, and `anonymous_artifact/` as supplementary material. Do not upload `PRIVATE_AUTHOR_CHECKLIST.md`, `official_template/`, the style zip, or any local workspace metadata.
