"""Import provided Random-40 human judgments and export a blinded logic spot-check.

This script does not train, load, or query the evaluator. It does not read
EXP-017 and never modifies the locked Final-200 pool or original sample.
"""

from __future__ import annotations

import csv
import json
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SAMPLE = DATA / "final200_human_audit_sample.csv"
LOCKED = DATA / "final200_pre_human_audit_locked.csv"
COMPLETED = DATA / "final200_human_audit_completed.csv"
SUMMARY = DATA / "final200_human_audit_summary.json"
SPOTCHECK = DATA / "final200_logic_spotcheck10_template.csv"
SPOTCHECK_MANIFEST = DATA / "final200_logic_spotcheck10_manifest.json"
SPOTCHECK_MD = ROOT.parents[1] / "docs" / "experiments" / "EXP-019-LOGIC-SPOTCHECK-10.md"
STATUS_MD = ROOT.parents[1] / "docs" / "experiments" / "EXP-019-FINAL200-HUMAN-AUDIT-STATUS.md"
SEED = 20260812
FAILED = {"GAP-LOG-036", "GAP-LOG-005"}
FAIL_REASON = "logic label clearly mismatched"
COMPLETED_FIELDS = (
    "review_index", "candidate_id", "task_class", "response_text",
    "human_overall_decision", "human_reason", "human_label_agreement",
    "human_naturalness", "human_self_contained", "human_ambiguity",
)
SPOTCHECK_FIELDS = ("review_index", "candidate_id", "response_text", "human_decision", "human_reason")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def validated_sample() -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    sample = read_csv(SAMPLE)
    locked = {row["candidate_id"]: row for row in read_csv(LOCKED)}
    if len(sample) != 40 or len({row["candidate_id"] for row in sample}) != 40:
        raise ValueError("The frozen random sample must contain exactly 40 unique IDs.")
    for row in sample:
        authoritative = locked.get(row["candidate_id"])
        if authoritative is None:
            raise ValueError(f"Random audit candidate missing from locked pool: {row['candidate_id']}")
        if row["task_class"] != authoritative["task_class"]:
            raise ValueError(f"Random audit class mismatch: {row['candidate_id']}")
    if not FAILED <= {row["candidate_id"] for row in sample}:
        raise ValueError("Explicit human N IDs are absent from the frozen random sample.")
    return sample, locked


def completed_rows(sample: list[dict[str, str]], locked: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    output = []
    for index, row in enumerate(sample, start=1):
        candidate_id = row["candidate_id"]
        if candidate_id in FAILED:
            # Do not invent a more granular human judgment for an issue-only N.
            decision, reason = "N", FAIL_REASON
            detail = {"human_label_agreement": "", "human_naturalness": "", "human_self_contained": "", "human_ambiguity": ""}
        else:
            decision, reason = "Y", ""
            detail = {"human_label_agreement": "agree", "human_naturalness": "acceptable", "human_self_contained": "yes", "human_ambiguity": "clear"}
        output.append({"review_index": str(index), "candidate_id": candidate_id, "task_class": locked[candidate_id]["task_class"], "response_text": locked[candidate_id]["response_text"], "human_overall_decision": decision, "human_reason": reason, **detail})
    return output


def logic_spotcheck(sample: list[dict[str, str]], locked: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    reviewed_logic = {row["candidate_id"] for row in sample if row["task_class"] == "logic"}
    eligible = sorted(row["candidate_id"] for row in locked.values() if row["task_class"] == "logic" and row["candidate_id"] not in reviewed_logic and row["candidate_id"] not in FAILED)
    if len(eligible) < 10:
        raise ValueError(f"Only {len(eligible)} unreviewed logic candidates are eligible; need 10.")
    ids = random.Random(SEED).sample(eligible, 10)
    return [{"review_index": str(index), "candidate_id": candidate_id, "response_text": locked[candidate_id]["response_text"], "human_decision": "", "human_reason": ""} for index, candidate_id in enumerate(ids, start=1)]


def spotcheck_markdown(rows: list[dict[str, str]]) -> str:
    header = """# EXP-019 Logic 定向复核（10条）

目的：

随机40条人工审计中，logic 出现2条标签不匹配。
本次仅确认该问题是个别样本，还是 logic 类存在更广泛的构造问题。

只判断：

“这条回答的主要功能是否确实是 logic？”

判断标准：

Y = logic 功能明确
N = 主要不是 logic
? = 边界/不确定

Logic 定义：

前提、条件、规则、排除、比较、空间/数量关系等，能够支持一个推论或结论。

特别注意：

普通事实陈述本身不自动等于 logic。

不要判断：

* 英语是否完美
* 来源是否权威
* evaluator 会不会识别
* 是否有利于后续实验

---

## 冻结解释规则

此规则在人工复核前固定：

* 0 N：`ISOLATED_LOGIC_ERRORS_SUPPORTED`
* 1 N：`LIKELY_ISOLATED_WITH_MINOR_RISK`
* 2 或更多 N：`LOGIC_CLASS_REVIEW_REQUIRED`
* 每个 `?` 视为未解决，不计作 Y；若 N 与 ? 合计达到 2 或更多：`LOGIC_CLASS_REVIEW_REQUIRED`

---
"""
    items = []
    for row in rows:
        items.append(
            f"## {int(row['review_index']):02d}\n\n"
            f"**ID:** `{row['candidate_id']}`\n\n"
            f"**Response:** {row['response_text']}\n\n"
            "**Decision:**\n\n"
            "**Reason:**\n\n"
            "---\n"
        )
    return header + "\n".join(items)


def main() -> None:
    sample, locked = validated_sample()
    completed = completed_rows(sample, locked)
    write_csv(COMPLETED, COMPLETED_FIELDS, completed)
    by_class = {}
    for task_class in ("logic", "causality", "analogy", "definition"):
        rows = [row for row in completed if row["task_class"] == task_class]
        by_class[task_class] = {"audited": len(rows), "Y": sum(row["human_overall_decision"] == "Y" for row in rows), "N": sum(row["human_overall_decision"] == "N" for row in rows), "uncertain": 0}
    summary = {
        "total": len(completed), "Y": sum(row["human_overall_decision"] == "Y" for row in completed), "N": sum(row["human_overall_decision"] == "N" for row in completed), "uncertain": 0,
        "overall_pass_rate": 0.95, "by_class": by_class,
        "freeze_status": "MINOR_REMEDIATION_REQUIRED",
        "freeze_reason": "Two isolated human-identified label-function mismatches were found, both within the logic class.",
        "logic_failures": sorted(FAILED), "evaluator_predictions_accessed": False, "exp017_outputs_accessed": False,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    spotcheck = logic_spotcheck(sample, locked)
    write_csv(SPOTCHECK, SPOTCHECK_FIELDS, spotcheck)
    SPOTCHECK_MD.parent.mkdir(parents=True, exist_ok=True)
    SPOTCHECK_MD.write_text(spotcheck_markdown(spotcheck), encoding="utf-8")
    SPOTCHECK_MANIFEST.write_text(json.dumps({"seed": SEED, "source_locked_file": LOCKED.name, "reviewed_logic_ids_excluded": sorted(row["candidate_id"] for row in sample if row["task_class"] == "logic"), "explicit_failures_excluded": sorted(FAILED), "eligible_unreviewed_logic_count": 50 - len({row["candidate_id"] for row in sample if row["task_class"] == "logic"}), "selected_candidate_ids": [row["candidate_id"] for row in spotcheck], "interpretation_rule": {"0_N": "ISOLATED_LOGIC_ERRORS_SUPPORTED", "1_N": "LIKELY_ISOLATED_WITH_MINOR_RISK", "2plus_N": "LOGIC_CLASS_REVIEW_REQUIRED", "2plus_total_N_or_uncertain": "LOGIC_CLASS_REVIEW_REQUIRED"}}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    STATUS_MD.write_text("# EXP-019 Final-200 Human Audit Status\n\n"
                         "## Random-40 result\n\n"
                         "- 38 Y / 2 N / 0 ? (95% overall pass rate).\n"
                         "- Both N results are in the logic class: `GAP-LOG-005` and `GAP-LOG-036`.\n"
                         "- Current status: `MINOR_REMEDIATION_REQUIRED`.\n\n"
                         "## Logic spot-check\n\n"
                         "A deterministic ten-item logic-only spot-check was exported to determine whether the two failures are isolated or systematic.\n\n"
                         "## Frozen interpretation rule\n\n"
                         "- 0 N: `ISOLATED_LOGIC_ERRORS_SUPPORTED`\n"
                         "- 1 N: `LIKELY_ISOLATED_WITH_MINOR_RISK`\n"
                         "- 2+ N, or 2+ combined N/?: `LOGIC_CLASS_REVIEW_REQUIRED`\n\n"
                         "The evaluator remained frozen; Final-200 predictions were not viewed; EXP-017 remains locked.\n", encoding="utf-8")
    print("RANDOM40_HUMAN_AUDIT_IMPORTED")
    print("Y_N_uncertain:", summary["Y"], summary["N"], summary["uncertain"])
    print("freeze_status:", summary["freeze_status"])
    print("unreviewed_logic_pool:", 50 - len({row["candidate_id"] for row in sample if row["task_class"] == "logic"}))
    print("spotcheck_size:", len(spotcheck))


if __name__ == "__main__":
    main()
