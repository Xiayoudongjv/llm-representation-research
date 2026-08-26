# Page budget

The official ICLR 2027 limit is nine pages for the main text, excluding references; the appendix follows the bibliography in the single-PDF build.

| Location | Required record |
|---|---|
| Main text start | Page 1 |
| Main text end | Page 8; within the nine-page limit |
| References start | Page 8 |
| Appendix start | Page 9, after the bibliography |
| AI-use statement | End matter of main paper |
| Reproducibility statement | End matter of main paper |

The current source uses the official two-column ICLR 2027 style, compact tables, and three main figures. If an external build exceeds nine main-text pages, only the following bounded compressions are permitted: shorten prose in the negative-evidence paragraph, move procedural detail to the appendix, reduce figure/table vertical whitespace, and retain exact values in Supplement S6. Do not remove the core direct/restricted-recovery decomposition, three-model result, registered negative evidence, or claim boundaries.

## Measured build (2026-08-26)

- Main text start page: 1
- Main text end page: 8
- Main text page count: 8
- References start page: 8
- References end page: 10
- Appendix start page: 10
- Appendix end page: 13
- Total PDF pages: 13
- Hard gate: `PASS` (8 <= 9)
- Build artifact: `build/paper.pdf`
- The main-text/reference boundary shares page 8; the appendix follows the
  references on page 10.

Local status: `LATEX_PAGE_COUNT_MEASURED`.
