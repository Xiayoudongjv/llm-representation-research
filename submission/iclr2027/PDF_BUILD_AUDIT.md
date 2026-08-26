# Paper A PDF Build Audit

PAPER_A_PDF_BUILD_STATUS = PASS
PDF_BUILD_BLOCKED_BY_LATEX_ENVIRONMENT = false

MIKTEX_DISCOVERY = PASS
LATEX_ENVIRONMENT = MiKTeX 25.12 at D:\Tools\MiKTeX
MIKTEX_ROOT = D:\Tools\MiKTeX
MIKTEX_BIN = D:\Tools\MiKTeX\miktex\bin\x64
PDFLATEX_PATH = D:\Tools\MiKTeX\miktex\bin\x64\pdflatex.exe
BIBTEX_PATH = D:\Tools\MiKTeX\miktex\bin\x64\bibtex.exe
LATEXMK_PATH = D:\Tools\MiKTeX\miktex\bin\x64\latexmk.exe
LATEXMK_STATUS = NOT_USABLE_PERL_UNAVAILABLE
LATEX_BUILD_COMMAND = pdflatex -> bibtex -> pdflatex -> pdflatex
LATEX_BUILD = PASS
LATEX_ENGINE = pdfTeX 1.40.28 (MiKTeX 25.12)

MAIN_TEXT_START_PAGE = 1
MAIN_TEXT_END_PAGE = 8
MAIN_TEXT_PAGE_COUNT = 8
REFERENCES_START_PAGE = 8
REFERENCES_END_PAGE = 10
APPENDIX_START_PAGE = 10
APPENDIX_END_PAGE = 13
TOTAL_PDF_PAGES = 13
MAIN_TEXT_PAGE_LIMIT = 9
MAIN_TEXT_PAGE_GATE = PASS

UNDEFINED_CITATIONS = 0
UNDEFINED_REFERENCES = 0
MISSING_PACKAGES = 0
MISSING_FILES = 0
MISSING_FIGURES = 0
OVERFULL_HBOX_COUNT = 0
MAJOR_OVERFULL_HBOX_COUNT = 0
UNDERFULL_WARNING_COUNT = 13

PDF_VISUAL_GATE = PASS
FIGURE1_READABLE = true
FIGURE2_READABLE = true
FIGURE3_READABLE = true
MAIN_TABLES_READABLE = true
APPENDIX_TABLES_READABLE = true

PDF_METADATA_GATE = PASS
PDF_ANONYMITY_GATE = PASS
ANONYMITY_PDF_SCAN = PASS
PDF_IDENTITY_LEAKS = 0
AI_USE_STATEMENT_VISIBLE = true
REPRODUCIBILITY_STATEMENT_VISIBLE = true

SCIENTIFIC_INVARIANCE_PASS = true
TITLE_CHANGED = false
ABSTRACT_SCIENCE_CHANGED = false
CONTRIBUTION_SCIENCE_CHANGED = false
C0_DEFINITION_CHANGED = false
D_DEFINITION_CHANGED = false
R_DEFINITION_CHANGED = false
DISTANCE_VALUES_CHANGED = false
SDI_VALUES_CHANGED = false
LOWD_VALUES_CHANGED = false
LOWD_PAIR_COUNTS_CHANGED = false
LOWD_POSITIVE_R_FRACTIONS_CHANGED = false
EXP023_STATUS_CHANGED = false
EXP024_STATUS_CHANGED = false
EXP025_ROLE_CHANGED = false
LLAMA_PROSPECTIVE_POSTHOC_BOUNDARY_CHANGED = false
CKA_PROMOTED = false
HEADROOM_INTERPRETATION_CHANGED = false
CROSS_TASK_CLAIM_RAISED = false
CANONICAL_NUMBERS_CHANGED = false
CANONICAL_STATUS_CHANGED = false
NEW_SCIENCE_CREATED = false

## Build and inspection notes

The final artifact is `build/paper.pdf` (626393 bytes). All thirteen pages were
rendered and inspected. Figures, main tables, appendix tables, captions, and
the anonymous-review header were readable with no observed clipping,
overlap, or cropped content. No overfull boxes and thirteen nonfatal
underfull warnings remain; they do not produce an observed visual failure.
MiKTeX installed only packages requested
by the build. BibTeX reported one nonfatal sorting warning for the locally
verified `freshhead2025localising` entry; no citation remained undefined.

The PDF text was checked against the final manuscript and supplement for the
load-bearing scientific values, definitions, roles, and claim boundaries.
The rendered package contains no local author identity, path, email, or
acknowledgement leak; generic LaTeX creator/producer metadata is permitted.

NEXT = UPLOAD_FREEZE_CANDIDATE_PDF_FOR_FINAL_TEXT_SIMILARITY_GATE

## Final copyedit and freeze-candidate gate

FINAL_COPYEDIT_GATE = PASS
FINAL_BUILD_GATE = PASS
FINAL_VISUAL_GATE = PASS
FINAL_ANONYMITY_GATE = PASS
FINAL_PDF_SHA256 = 83511ecdbc2e611e23a29ab8c8dfc0e1d5e3c88258ce2508db16336a86a8b61f
FINAL_PDF_BYTES = 626393
FINAL_MAIN_TEXT_PAGES = 8
FINAL_TOTAL_PDF_PAGES = 13
SECTION_4_1_DANGLING_COLON = FIXED
OFF_DIAGONAL_UNIT_AMBIGUITY = FIXED
PROJECT_INTERNAL_STYLE_CLEANUP = APPLIED
EMPIRICAL_DISSOCIATION_CLEANUP = APPLIED
FORMAL_TEXT_SIMILARITY_CHECK = PENDING
PAPER_A_FINAL_PDF_FREEZE_CANDIDATE = true

The final copyedit made only bounded prose and reproducibility clarifications:
the Section 4.1 lead-in now points to Table 1, Section 3.7 names the
registered off-diagonal matrix entries explicitly, and limited internal
project-name wording was normalized. No canonical number, status, claim, or
scientific definition changed. The empirical dissociation definition was
removed without introducing a stronger construct. The PDF skill's marker
script could not run because `node` is not installed in this environment;
local MiKTeX build and PDF validation completed successfully.
