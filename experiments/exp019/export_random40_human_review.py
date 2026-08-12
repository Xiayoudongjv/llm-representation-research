"""Export the frozen EXP-019 random-40 sample as a blank Markdown review form.

The locked Final-200 pool is the only response-text authority. Existing audit
decisions are deliberately ignored: this exporter creates a separate blank
human-readable form and companion CSV without changing the original sample.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SAMPLE = DATA / "final200_human_audit_sample.csv"
LOCKED = DATA / "final200_pre_human_audit_locked.csv"
TEMPLATE = DATA / "final200_random40_human_review_template.csv"
MARKDOWN = ROOT.parents[1] / "docs" / "experiments" / "EXP-019-FINAL200-RANDOM40-HUMAN-REVIEW.md"
TEMPLATE_FIELDS = ("review_index", "candidate_id", "task_class", "response_text", "human_decision", "human_reason")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def validated_locked_sample() -> list[dict[str, str]]:
    """Return sample rows with locked text, after strict ID/class validation."""
    sample = read_csv(SAMPLE)
    locked = {row["candidate_id"]: row for row in read_csv(LOCKED)}
    if len(sample) != 40 or len({row["candidate_id"] for row in sample}) != 40:
        raise ValueError("Frozen random-audit sample must contain exactly 40 unique candidate IDs.")
    output = []
    for row in sample:
        candidate_id = row["candidate_id"]
        authoritative = locked.get(candidate_id)
        if authoritative is None:
            raise ValueError(f"Sample candidate is absent from locked Final-200: {candidate_id}")
        if row["task_class"] != authoritative["task_class"]:
            raise ValueError(f"Sample class differs from locked Final-200: {candidate_id}")
        output.append({"candidate_id": candidate_id, "task_class": authoritative["task_class"], "response_text": authoritative["response_text"]})
    return output


def markdown_text(rows: list[dict[str, str]]) -> str:
    guide = """# EXP-019 Final-200 随机40条人工审核

## 审核方式

对每条进行综合判断，只填写：

* `Y` = 通过
* `N` = 有明显问题
* `?` = 不确定

`Y` 表示综合认为：

1. 当前 task_class 基本合理；
2. 英语至少达到正常、可接受的短回答水平；
3. 句子脱离原始 prompt 后仍能独立理解；
4. 不存在明显的类别歧义。

注意：

* `Y` 不代表句子必须完美；
* 不需要为了措辞不够优美而判 N；
* 不需要进行系统事实查证；
* 如果类别功能明显不清楚，可以填 `?` 或 `N`；
* 不要修改原始 Response；
* 正常样本只写 Decision 即可；
* 只有 N 或 ? 建议写简短备注。

---

## 类别参考

**logic**
前提、条件、规则、排除、比较或关系能够支持某个结论。

**causality**
表达原因产生结果，或描述作用机制。

**analogy**
表达两组事物或关系之间的对应。

**definition**
说明一个概念是什么、属于什么类别、或其定义性功能/属性。

提醒：

* 普通事实陈述不自动等于 logic；
* 带有 `is` 不自动等于 definition；
* 重点判断整句话主要承担什么功能。

---
"""
    items = []
    for index, row in enumerate(rows, start=1):
        items.append(
            f"## {index:02d}\n\n"
            f"**ID:** `{row['candidate_id']}`\n\n"
            f"**Class:** `{row['task_class']}`\n\n"
            f"**Response:** {row['response_text']}\n\n"
            "**Decision:**\n\n"
            "**Reason:**\n\n"
            "---\n"
        )
    summary = """\n# 审核后汇总

Y：
N：
?：

需要重点说明的问题：

-
-
-
"""
    return guide + "\n".join(items) + summary


def main() -> None:
    rows = validated_locked_sample()
    MARKDOWN.parent.mkdir(parents=True, exist_ok=True)
    MARKDOWN.write_text(markdown_text(rows), encoding="utf-8")
    write_csv(TEMPLATE, TEMPLATE_FIELDS, [
        {"review_index": str(index), "candidate_id": row["candidate_id"], "task_class": row["task_class"], "response_text": row["response_text"], "human_decision": "", "human_reason": ""}
        for index, row in enumerate(rows, start=1)
    ])
    print("RANDOM40_REVIEW_EXPORT_COMPLETE")
    print("sample_rows:", len(rows))
    print("class_counts:", dict(Counter(row["task_class"] for row in rows)))
    print("stale_text_corrections_used_for_export:", sum(row["response_text"] != sample["response_text"] for row, sample in zip(rows, read_csv(SAMPLE), strict=True)))


if __name__ == "__main__":
    main()
