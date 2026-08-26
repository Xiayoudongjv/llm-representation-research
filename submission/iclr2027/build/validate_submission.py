"""Static checks for the anonymous ICLR 2027 package; no model access."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
ARTIFACT = ROOT / "anonymous_artifact"


def main() -> int:
    required = [
        PAPER / "main.tex",
        ROOT / "appendix" / "appendix.tex",
        PAPER / "references.bib",
        ARTIFACT / "manifest.json",
    ]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing:
        print("MISSING=" + ",".join(missing))
        return 1

    main_tex = (PAPER / "main.tex").read_text(encoding="utf-8")
    appendix = (ROOT / "appendix" / "appendix.tex").read_text(encoding="utf-8")
    bib = (PAPER / "references.bib").read_text(encoding="utf-8")
    all_tex = main_tex + "\n" + appendix
    keys = set(re.findall(r"\\cite[tp]?\{([^}]+)\}", all_tex))
    keys = {key.strip() for group in keys for key in group.split(",")}
    bib_keys = set(re.findall(r"^@\w+\{([^,]+),", bib, re.MULTILINE))
    missing_citations = sorted(keys - bib_keys)
    figures = re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", all_tex)
    missing_figures = []
    for figure in figures:
        base = PAPER / figure if "figures/" not in figure else ROOT / "appendix" / figure
        if not base.exists():
            missing_figures.append(figure)
    identity_patterns = [r"D:\\\\Research", r"C:\\\\Users", r"Xiayo", r"github\.com", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}"]
    identity_hits = [pattern for pattern in identity_patterns if re.search(pattern, all_tex + bib, re.IGNORECASE)]
    manifest = json.loads((ARTIFACT / "manifest.json").read_text(encoding="utf-8"))
    checks = {
        "anonymous_style": "iclrfinalcopy" not in main_tex,
        "citations_resolved": not missing_citations,
        "figures_present": not missing_figures,
        "artifact_manifest_json": isinstance(manifest, dict),
        "identity_scan_clean_for_submission_text": not identity_hits,
        "appendix_after_bibliography": "\\bibliography{references}" in main_tex and "\\appendix" in main_tex,
    }
    print(json.dumps({"checks": checks, "missing_citations": missing_citations, "missing_figures": missing_figures, "identity_hits": identity_hits}, indent=2, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
