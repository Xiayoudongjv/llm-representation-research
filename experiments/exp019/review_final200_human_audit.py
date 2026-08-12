"""Fast, resumable human QA for the locked EXP-019 Final-200 candidate pool.

This tool only records keyboard-entered human judgments. It never loads an
evaluator, produces predictions, reads EXP-017, or modifies the locked pool.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path
from typing import Callable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
LOCKED_POOL = DATA / "final200_pre_human_audit_locked.csv"
SAMPLE = DATA / "final200_human_audit_sample.csv"
SIMILARITY_REVIEW = DATA / "final200_similarity_review.csv"
AUDIT_FIELDS = ("human_label_agreement", "human_naturalness", "human_self_contained", "human_ambiguity", "human_notes")
SIMILARITY_FIELDS = ("candidate_id", "task_class", "response_text", "flag_type", "matched_candidate_id", "similarity_value_if_available", "human_redundancy_decision", "human_notes")
Input = Callable[[str], str]
Output = Callable[..., None]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|\d+", text.casefold())


def is_completed(row: dict[str, str]) -> bool:
    return all(row[field] for field in AUDIT_FIELDS[:4])


def fast_pass_compatible(row: dict[str, str]) -> bool:
    """Count the pre-existing field combination written by a one-key pass."""
    return is_completed(row) and all((row["human_label_agreement"] == "agree", row["human_naturalness"] == "acceptable", row["human_self_contained"] == "yes", row["human_ambiguity"] == "clear", not row["human_notes"]))


def prepare_similarity_review(pool_path: Path = LOCKED_POOL, output_path: Path = SIMILARITY_REVIEW) -> list[dict[str, str]]:
    """Create a blank, deduplicated mechanical supplement from the locked pool."""
    pool = read_csv(pool_path)
    by_id = {row["candidate_id"]: row for row in pool}
    groups: defaultdict[str, list[str]] = defaultdict(list)
    for row in pool:
        prefix = " ".join(words(row["response_text"])[:3])
        if prefix:
            groups[prefix].append(row["candidate_id"])
    flags: defaultdict[str, set[str]] = defaultdict(set)
    matches: defaultdict[str, set[str]] = defaultdict(set)
    values: defaultdict[str, list[str]] = defaultdict(list)
    for ids in groups.values():
        if len(ids) > 1:
            for candidate_id in ids:
                flags[candidate_id].add("repeated_three_word_prefix")
                matches[candidate_id].update(other for other in ids if other != candidate_id)
    vector = TfidfVectorizer(analyzer="char", ngram_range=(3, 5), lowercase=True)
    matrix = vector.fit_transform([row["response_text"] for row in pool])
    similarity = cosine_similarity(matrix)
    for left in range(len(pool)):
        for right in range(left + 1, len(pool)):
            value = float(similarity[left, right])
            if value >= 0.55:
                left_id, right_id = pool[left]["candidate_id"], pool[right]["candidate_id"]
                flags[left_id].add("tfidf_char_cosine_ge_0.55")
                flags[right_id].add("tfidf_char_cosine_ge_0.55")
                matches[left_id].add(right_id)
                matches[right_id].add(left_id)
                values[left_id].append(f"{value:.4f}")
                values[right_id].append(f"{value:.4f}")
    rows = [{
        "candidate_id": candidate_id,
        "task_class": by_id[candidate_id]["task_class"],
        "response_text": by_id[candidate_id]["response_text"],
        "flag_type": ";".join(sorted(flags[candidate_id])),
        "matched_candidate_id": ";".join(sorted(matches[candidate_id])),
        "similarity_value_if_available": ";".join(sorted(set(values[candidate_id]))),
        "human_redundancy_decision": "",
        "human_notes": "",
    } for candidate_id in sorted(flags)]
    write_csv(output_path, list(SIMILARITY_FIELDS), rows)
    return rows


def synchronize_sample_with_locked_pool(rows: list[dict[str, str]], locked_path: Path) -> None:
    """Synchronize unreviewed display text while protecting completed judgments."""
    locked = {row["candidate_id"]: row for row in read_csv(locked_path)}
    for row in rows:
        expected = locked.get(row["candidate_id"])
        if expected is None:
            raise ValueError(f"Frozen audit ID is absent from locked pool: {row['candidate_id']}")
        for field in ("task_class", "response_text", "provenance", "topic_domain"):
            if row[field] != expected[field]:
                if any(row[field_name] for field_name in AUDIT_FIELDS):
                    raise ValueError(f"Completed audit row differs from locked pool: {row['candidate_id']}")
                row[field] = expected[field]


def ask_allowed(prompt: str, allowed: set[str], input_func: Input, output_func: Output, *, allow_blank: bool = False) -> str:
    while True:
        value = input_func(prompt).strip().lower()
        if allow_blank and not value:
            return ""
        if value in allowed:
            return value
        output_func("Allowed values: " + ", ".join(sorted(allowed)))


def detailed_review(input_func: Input, output_func: Output) -> dict[str, str]:
    """The original detailed four-field path for multiple issues."""
    return {
        "human_label_agreement": ask_allowed("label [agree/disagree/ambiguous]: ", {"agree", "disagree", "ambiguous"}, input_func, output_func),
        "human_naturalness": ask_allowed("naturalness [natural/acceptable/awkward]: ", {"natural", "acceptable", "awkward"}, input_func, output_func),
        "human_self_contained": ask_allowed("self-contained [yes/no]: ", {"yes", "no"}, input_func, output_func),
        "human_ambiguity": ask_allowed("ambiguity [clear/borderline/ambiguous]: ", {"clear", "borderline", "ambiguous"}, input_func, output_func),
        "human_notes": input_func("notes [optional]: ").strip(),
    }


def collect_issue(input_func: Input, output_func: Output) -> dict[str, str] | None:
    """Collect only the fields necessary for the human-selected issue mode."""
    choice = ask_allowed("issue [1 label/2 language/3 self-contained/4 ambiguity/5 multiple/b back]: ", {"1", "2", "3", "4", "5", "b"}, input_func, output_func)
    if choice == "b":
        return None
    if choice == "5":
        return detailed_review(input_func, output_func)
    result = {"human_label_agreement": "agree", "human_naturalness": "acceptable", "human_self_contained": "yes", "human_ambiguity": "clear", "human_notes": ""}
    if choice == "1":
        label = ask_allowed("label [d disagree/a ambiguous]: ", {"d", "a"}, input_func, output_func)
        result["human_label_agreement"] = "disagree" if label == "d" else "ambiguous"
        result["human_ambiguity"] = "clear" if label == "d" else "ambiguous"
    elif choice == "2":
        language = ask_allowed("language [w awkward/c acceptable but concerning]: ", {"w", "c"}, input_func, output_func)
        result["human_naturalness"] = "awkward" if language == "w" else "acceptable"
        result["human_self_contained"] = ask_allowed("self-contained [y/n]: ", {"y", "n"}, input_func, output_func)
        result["human_self_contained"] = "yes" if result["human_self_contained"] == "y" else "no"
        ambiguity = ask_allowed("ambiguity [c clear/b borderline/a ambiguous]: ", {"c", "b", "a"}, input_func, output_func)
        result["human_ambiguity"] = {"c": "clear", "b": "borderline", "a": "ambiguous"}[ambiguity]
    elif choice == "3":
        language = ask_allowed("language [Enter acceptable/w awkward]: ", {"w"}, input_func, output_func, allow_blank=True)
        result["human_naturalness"] = "awkward" if language == "w" else "acceptable"
        result["human_self_contained"] = "no"
        label = ask_allowed("label [a agree/d disagree/m ambiguous]: ", {"a", "d", "m"}, input_func, output_func)
        result["human_label_agreement"] = {"a": "agree", "d": "disagree", "m": "ambiguous"}[label]
        ambiguity = ask_allowed("ambiguity [c clear/b borderline/a ambiguous]: ", {"c", "b", "a"}, input_func, output_func)
        result["human_ambiguity"] = {"c": "clear", "b": "borderline", "a": "ambiguous"}[ambiguity]
    elif choice == "4":
        label = ask_allowed("label [Enter agree/d disagree/m ambiguous]: ", {"d", "m"}, input_func, output_func, allow_blank=True)
        result["human_label_agreement"] = {"": "agree", "d": "disagree", "m": "ambiguous"}[label]
        ambiguity = ask_allowed("ambiguity [b borderline/a ambiguous]: ", {"b", "a"}, input_func, output_func)
        result["human_ambiguity"] = "borderline" if ambiguity == "b" else "ambiguous"
    result["human_notes"] = input_func("notes [optional]: ").strip()
    return result


def confirm_issue(result: dict[str, str], input_func: Input, output_func: Output) -> str:
    output_func("label:", result["human_label_agreement"])
    output_func("naturalness:", result["human_naturalness"])
    output_func("self-contained:", result["human_self_contained"])
    output_func("ambiguity:", result["human_ambiguity"])
    output_func("notes:", result["human_notes"] or "(blank)")
    return ask_allowed("[y] save [n] edit [c] cancel: ", {"y", "n", "c"}, input_func, output_func)


def run_review(sample_path: Path = SAMPLE, locked_path: Path = LOCKED_POOL, input_func: Input = input, output_func: Output = print) -> None:
    """Run the fast random-40 audit, preserving completed rows and resume state."""
    rows = read_csv(sample_path)
    synchronize_sample_with_locked_pool(rows, locked_path)
    write_csv(sample_path, list(rows[0]) if rows else [], rows)
    output_func(f"progress: {sum(is_completed(row) for row in rows)}/{len(rows)} completed")
    for row in rows:
        if is_completed(row):
            continue
        while True:
            output_func("\n---")
            output_func("candidate_id:", row["candidate_id"])
            output_func("task_class:", row["task_class"])
            output_func("response_text:", row["response_text"])
            output_func("provenance/topic:", f"{row['provenance']} | {row['topic_domain']}")
            action = ask_allowed("[y] pass [n] issue [s] skip [q] save & quit: ", {"y", "n", "s", "q"}, input_func, output_func)
            if action == "q":
                write_csv(sample_path, list(rows[0]), rows)
                output_func("saved; quitting")
                return
            if action == "s":
                break
            if action == "y":
                row.update({"human_label_agreement": "agree", "human_naturalness": "acceptable", "human_self_contained": "yes", "human_ambiguity": "clear", "human_notes": ""})
                write_csv(sample_path, list(rows[0]), rows)
                output_func("saved")
                break
            result = collect_issue(input_func, output_func)
            if result is None:
                continue
            confirmation = confirm_issue(result, input_func, output_func)
            if confirmation == "c":
                break
            if confirmation == "n":
                continue
            row.update(result)
            write_csv(sample_path, list(rows[0]), rows)
            output_func("saved")
            break
    write_csv(sample_path, list(rows[0]) if rows else [], rows)
    output_func(f"progress: {sum(is_completed(row) for row in rows)}/{len(rows)} completed")


def run_similarity_review(similarity_path: Path = SIMILARITY_REVIEW, locked_path: Path = LOCKED_POOL, input_func: Input = input, output_func: Output = print) -> None:
    """Run fast human review for the flagged similarity candidates."""
    rows = read_csv(similarity_path)
    locked = {row["candidate_id"]: row for row in read_csv(locked_path)}
    output_func(f"similarity progress: {sum(bool(row['human_redundancy_decision']) for row in rows)}/{len(rows)} completed")
    mapping = {"y": "distinct_enough", "n": "redundant", "u": "uncertain"}
    for row in rows:
        if row["human_redundancy_decision"]:
            continue
        output_func("\n---")
        output_func("candidate_id:", row["candidate_id"])
        output_func("response_text:", row["response_text"])
        output_func("flag_type:", row["flag_type"])
        for matched_id in filter(None, row["matched_candidate_id"].split(";")):
            output_func(f"matched_response [{matched_id}]:", locked[matched_id]["response_text"])
        action = ask_allowed("[y] distinct enough [n] redundant [u] uncertain [s] skip [q] save & quit: ", {"y", "n", "u", "s", "q"}, input_func, output_func)
        if action == "q":
            write_csv(similarity_path, list(rows[0]), rows)
            output_func("saved; quitting")
            return
        if action == "s":
            continue
        row["human_redundancy_decision"] = mapping[action]
        row["human_notes"] = ""
        write_csv(similarity_path, list(rows[0]), rows)
        output_func("saved")
    write_csv(similarity_path, list(rows[0]) if rows else [], rows)
    output_func(f"similarity progress: {sum(bool(row['human_redundancy_decision']) for row in rows)}/{len(rows)} completed")


def status(sample_path: Path = SAMPLE, similarity_path: Path = SIMILARITY_REVIEW, output_func: Output = print) -> None:
    """Report completion counts without changing any review file."""
    random_rows = read_csv(sample_path)
    similarity_rows = read_csv(similarity_path)
    completed = sum(is_completed(row) for row in random_rows)
    decisions = defaultdict(int)
    for row in similarity_rows:
        decisions[row["human_redundancy_decision"]] += 1
    output_func("Random audit:")
    output_func(f"  completed / total: {completed}/{len(random_rows)}")
    output_func(f"  remaining: {len(random_rows) - completed}")
    output_func(f"  pass-fast-compatible count: {sum(fast_pass_compatible(row) for row in random_rows)}")
    output_func(f"  issue count: {completed - sum(fast_pass_compatible(row) for row in random_rows)}")
    output_func("Similarity:")
    output_func(f"  completed / total: {sum(bool(row['human_redundancy_decision']) for row in similarity_rows)}/{len(similarity_rows)}")
    output_func(f"  distinct: {decisions['distinct_enough']}")
    output_func(f"  redundant: {decisions['redundant']}")
    output_func(f"  uncertain: {decisions['uncertain']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-similarity-review", action="store_true")
    parser.add_argument("--review", action="store_true")
    parser.add_argument("--review-similarity", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--pool", type=Path, default=LOCKED_POOL)
    parser.add_argument("--similarity-output", type=Path, default=SIMILARITY_REVIEW)
    args = parser.parse_args()
    if not any((args.prepare_similarity_review, args.review, args.review_similarity, args.status)):
        parser.error("choose --prepare-similarity-review, --review, --review-similarity, or --status")
    if args.prepare_similarity_review:
        output = prepare_similarity_review(args.pool, args.similarity_output)
        print("similarity_review_rows:", len(output))
    if args.review:
        run_review()
    if args.review_similarity:
        run_similarity_review()
    if args.status:
        status()


if __name__ == "__main__":
    main()
