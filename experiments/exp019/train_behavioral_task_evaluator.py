"""Train and freeze the EXP-019 procedural behavioral targetness evaluator.

Only ``data/behavioral_targetness_dataset.csv`` is opened for model fitting,
selection, or evaluation.  Final-200 and EXP-017 paths are named below solely
as an explicit access guard and are never opened by this script.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import joblib
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, confusion_matrix, f1_score, precision_recall_fscore_support
from sklearn.pipeline import FeatureUnion, Pipeline

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.behavioral_task_evaluator import CLASS_ORDER, MODEL_COLUMN_BY_CLASS, SKLEARN_MODEL_CLASS_ORDER


EXP_DIR = Path(__file__).resolve().parent
DATASET = EXP_DIR / "data" / "behavioral_targetness_dataset.csv"
RESULTS = EXP_DIR / "results"
ARTIFACTS = EXP_DIR / "artifacts"
CONFIG = EXP_DIR / "evaluator_frozen_config.json"
FORBIDDEN_PATHS = (
    ROOT / "experiments" / "exp019" / "data" / "final200_pre_human_audit_locked.csv",
    ROOT / "experiments" / "exp019" / "data" / "final200_frozen.csv",
    ROOT / "results" / "exp017",
    ROOT / "experiments" / "exp017",
)
SEED = 20260812


def read_dataset() -> list[dict[str, str]]:
    """Read the single permitted procedural corpus and no other example text."""
    if DATASET.resolve() in {path.resolve() for path in FORBIDDEN_PATHS}:
        raise RuntimeError("Forbidden path requested.")
    with DATASET.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 760:
        raise ValueError(f"Expected 760 corpus rows, found {len(rows)}")
    return rows


def split_rows(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    return {split: [row for row in rows if row["split"] == split] for split in ("train", "validation", "test")}


def hash_rows(rows: list[dict[str, str]]) -> str:
    canonical = "\n".join("\t".join(row[key] for key in ("example_id", "content_family_id", "task_class", "response_text", "split")) for row in sorted(rows, key=lambda item: item["example_id"]))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_pipeline(word_range: tuple[int, int], word_min_df: int, char_range: tuple[int, int], char_min_df: int, c_value: float) -> Pipeline:
    features = FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=word_range, min_df=word_min_df, sublinear_tf=True, lowercase=True)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=char_range, min_df=char_min_df, sublinear_tf=True, lowercase=True)),
    ])
    # scikit-learn 1.9 removed ``multi_class``; lbfgs selects multinomial
    # behavior automatically for this four-class target.
    classifier = LogisticRegression(C=c_value, class_weight=None, max_iter=2000, random_state=SEED, solver="lbfgs")
    return Pipeline([("features", features), ("classifier", classifier)])


def metrics(y_true: list[str], y_pred: list[str], probabilities=None) -> dict[str, object]:
    precision, recall, f1, support = precision_recall_fscore_support(y_true, y_pred, labels=CLASS_ORDER, zero_division=0)
    result: dict[str, object] = {
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, labels=CLASS_ORDER, average="macro", zero_division=0)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "per_class": {label: {"precision": float(precision[index]), "recall": float(recall[index]), "f1": float(f1[index]), "support": int(support[index])} for index, label in enumerate(CLASS_ORDER)},
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=CLASS_ORDER).tolist(),
    }
    if probabilities is not None:
        predicted_confidence = probabilities.max(axis=1)
        result["probability_calibration_descriptive"] = {
            "mean_max_probability": float(predicted_confidence.mean()),
            "median_max_probability": float(__import__("numpy").median(predicted_confidence)),
            "mean_probability_assigned_to_true_class": float(__import__("numpy").mean([probabilities[index, MODEL_COLUMN_BY_CLASS[label]] for index, label in enumerate(y_true)])),
        }
    return result


def simpler_key(row: dict[str, object]) -> tuple[int, int, int, int, float]:
    return (int(row["word_ngram_range"].split(",")[1]), int(row["char_ngram_range"].split(",")[1]), -int(row["word_min_df"]), -int(row["char_min_df"]), float(row["C"]))


def select_configuration(search_rows: list[dict[str, object]]) -> dict[str, object]:
    best_ba = max(float(row["validation_balanced_accuracy"]) for row in search_rows)
    tied = [row for row in search_rows if best_ba - float(row["validation_balanced_accuracy"]) <= 0.005]
    best_f1 = max(float(row["validation_macro_f1"]) for row in tied)
    tied = [row for row in tied if best_f1 - float(row["validation_macro_f1"]) <= 1e-12]
    best_min_recall = max(float(row["validation_min_class_recall"]) for row in tied)
    tied = [row for row in tied if best_min_recall - float(row["validation_min_class_recall"]) <= 1e-12]
    return sorted(tied, key=simpler_key)[0]


def feature_audit(pipeline: Pipeline) -> list[dict[str, object]]:
    names = pipeline.named_steps["features"].get_feature_names_out()
    coef = pipeline.named_steps["classifier"].coef_
    rows = []
    for class_index, label in enumerate(SKLEARN_MODEL_CLASS_ORDER):
        positive = coef[class_index].argsort()[-10:][::-1]
        negative = coef[class_index].argsort()[:10]
        for direction, indices in (("positive", positive), ("negative", negative)):
            for rank, index in enumerate(indices, start=1):
                name = str(names[index])
                rows.append({"task_class": label, "direction": direction, "rank": rank, "feature": name, "coefficient": float(coef[class_index, index]), "feature_group": "word" if name.startswith("word__") else "character"})
    return rows


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite", action="store_true", help="Permit a deliberate reproducibility rerun only.")
    args = parser.parse_args()
    if CONFIG.exists() and not args.overwrite:
        raise RuntimeError("Frozen config already exists; refuse to retune or overwrite without --overwrite.")

    rows = read_dataset()
    split = split_rows(rows)
    expected = {"train": 480, "validation": 120, "test": 160}
    if {key: len(value) for key, value in split.items()} != expected:
        raise ValueError("Frozen split sizes differ from the canonical protocol.")
    train_text, train_y = [row["response_text"] for row in split["train"]], [row["task_class"] for row in split["train"]]
    val_text, val_y = [row["response_text"] for row in split["validation"]], [row["task_class"] for row in split["validation"]]

    search_rows: list[dict[str, object]] = []
    for word_range in ((1, 1), (1, 2)):
        for word_min_df in (1, 2):
            for char_range in ((3, 5), (3, 6)):
                for char_min_df in (1, 2):
                    for c_value in (0.1, 0.3, 1.0, 3.0, 10.0):
                        pipeline = build_pipeline(word_range, word_min_df, char_range, char_min_df, c_value)
                        pipeline.fit(train_text, train_y)
                        val_pred = pipeline.predict(val_text)
                        val_metrics = metrics(val_y, list(val_pred))
                        search_rows.append({"word_ngram_range": f"{word_range[0]},{word_range[1]}", "word_min_df": word_min_df, "char_analyzer": "char_wb", "char_ngram_range": f"{char_range[0]},{char_range[1]}", "char_min_df": char_min_df, "sublinear_tf": True, "lowercase": True, "C": c_value, "validation_balanced_accuracy": val_metrics["balanced_accuracy"], "validation_macro_f1": val_metrics["macro_f1"], "validation_min_class_recall": min(item["recall"] for item in val_metrics["per_class"].values()), "validation_accuracy": val_metrics["accuracy"], "selection_data": "validation_only"})
    selected = select_configuration(search_rows)
    RESULTS.mkdir(parents=True, exist_ok=True)
    write_csv(RESULTS / "evaluator_validation_search.csv", list(search_rows[0]), search_rows)

    word_range = tuple(map(int, str(selected["word_ngram_range"]).split(",")))
    char_range = tuple(map(int, str(selected["char_ngram_range"]).split(",")))
    selected_pipeline = build_pipeline(word_range, int(selected["word_min_df"]), char_range, int(selected["char_min_df"]), float(selected["C"]))
    selected_pipeline.fit(train_text, train_y)
    if tuple(selected_pipeline.classes_) != SKLEARN_MODEL_CLASS_ORDER:
        raise RuntimeError(f"Unexpected fitted model class order: {tuple(selected_pipeline.classes_)}")
    selected_val_metrics = metrics(val_y, list(selected_pipeline.predict(val_text)))
    config = {"class_order": list(CLASS_ORDER), "sklearn_model_class_order": list(SKLEARN_MODEL_CLASS_ORDER), "evaluator_family": "word + character TF-IDF + multinomial LogisticRegression", "word_tfidf": {"ngram_range": list(word_range), "min_df": int(selected["word_min_df"]), "sublinear_tf": True, "lowercase": True}, "char_tfidf": {"analyzer": "char_wb", "ngram_range": list(char_range), "min_df": int(selected["char_min_df"]), "sublinear_tf": True, "lowercase": True}, "logistic_regression": {"C": float(selected["C"]), "class_weight": None, "random_state": SEED, "max_iter": 2000, "solver": "lbfgs", "multi_class": "multinomial (automatic lbfgs behavior in sklearn 1.9)"}, "preprocessing": "raw response_text only; no labels, IDs, provenance, topics, prompts, or length metadata", "random_seed": SEED, "train_split_identity_hash": hash_rows(split["train"]), "validation_split_identity_hash": hash_rows(split["validation"]), "selection_metric": "balanced_accuracy, then macro_F1, minimum per-class recall, and simpler configuration within 0.005 balanced accuracy", "selected_validation_metrics": selected_val_metrics, "timestamp_utc": datetime.now(timezone.utc).isoformat(), "final200_accessed_for_selection": False, "exp017_accessed_for_selection": False, "test_evaluated_at_selection": False, "sklearn_version": sklearn.__version__}
    CONFIG.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    test_text, test_y = [row["response_text"] for row in split["test"]], [row["task_class"] for row in split["test"]]
    test_probabilities = selected_pipeline.predict_proba(test_text)
    test_pred = selected_pipeline.predict(test_text)
    test_metrics = metrics(test_y, list(test_pred), test_probabilities)
    test_metrics.update({"evaluation_timestamp_utc": datetime.now(timezone.utc).isoformat(), "protocol": "selected on validation; fit train only; evaluated procedural test once", "procedural_test_status": "PROCEDURAL_TEST_PASSED" if test_metrics["balanced_accuracy"] >= 0.70 and test_metrics["macro_f1"] >= 0.70 and all(item["recall"] >= 0.60 for item in test_metrics["per_class"].values()) else "PROCEDURAL_TEST_FAILED", "final200_accessed": False, "exp017_accessed": False})
    (RESULTS / "evaluator_procedural_test_metrics.json").write_text(json.dumps(test_metrics, indent=2) + "\n", encoding="utf-8")
    write_csv(RESULTS / "evaluator_confusion_matrix.csv", ["true_task_class", *CLASS_ORDER], [{"true_task_class": label, **dict(zip(CLASS_ORDER, test_metrics["confusion_matrix"][index], strict=True))} for index, label in enumerate(CLASS_ORDER)])
    write_csv(RESULTS / "evaluator_per_class_metrics.csv", ["task_class", "precision", "recall", "f1", "support"], [{"task_class": label, **values} for label, values in test_metrics["per_class"].items()])

    lexical = [row for row in split["test"] if row["lexical_challenge"] == "true"]
    lexical_y = [row["task_class"] for row in lexical]
    lexical_pred = selected_pipeline.predict([row["response_text"] for row in lexical])
    lexical_metrics = metrics(lexical_y, list(lexical_pred))
    lexical_metrics.update({"challenge_rows": len(lexical), "class_counts": dict(Counter(lexical_y)), "comparison_split": "procedural_test", "balanced_accuracy_drop_from_procedural_test": float(test_metrics["balanced_accuracy"] - lexical_metrics["balanced_accuracy"]), "criterion_balanced_accuracy_min": 0.55, "criterion_drop_max": 0.15, "status": "LEXICAL_CHALLENGE_PASSED" if lexical_metrics["balanced_accuracy"] >= 0.55 and test_metrics["balanced_accuracy"] - lexical_metrics["balanced_accuracy"] <= 0.15 else "LEXICAL_CHALLENGE_FAILED", "frozen_subset": "dataset lexical_challenge=true AND split=test"})
    (RESULTS / "evaluator_lexical_challenge_metrics.json").write_text(json.dumps(lexical_metrics, indent=2) + "\n", encoding="utf-8")

    audit_rows = feature_audit(selected_pipeline)
    feature_summary = {"word": float(abs(selected_pipeline.named_steps["classifier"].coef_[:, :len(selected_pipeline.named_steps["features"].transformer_list[0][1].get_feature_names_out())]).sum()), "character": float(abs(selected_pipeline.named_steps["classifier"].coef_[:, len(selected_pipeline.named_steps["features"].transformer_list[0][1].get_feature_names_out()):]).sum())}
    for row in audit_rows:
        row["word_feature_abs_coefficient_sum"] = feature_summary["word"]
        row["character_feature_abs_coefficient_sum"] = feature_summary["character"]
    write_csv(RESULTS / "evaluator_feature_audit.csv", ["task_class", "direction", "rank", "feature", "coefficient", "feature_group", "word_feature_abs_coefficient_sum", "character_feature_abs_coefficient_sum"], audit_rows)

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    artifact_path = ARTIFACTS / "evaluator_tfidf_logreg.joblib"
    joblib.dump(selected_pipeline, artifact_path)
    (ARTIFACTS / "evaluator_label_mapping.json").write_text(json.dumps({"class_order": list(CLASS_ORDER), "sklearn_version": sklearn.__version__, "artifact": artifact_path.name}, indent=2) + "\n", encoding="utf-8")
    status = "EVALUATOR_DEV_PASSED" if test_metrics["procedural_test_status"] == "PROCEDURAL_TEST_PASSED" and lexical_metrics["status"] == "LEXICAL_CHALLENGE_PASSED" else "EVALUATOR_DEV_FAILED"
    # No frozen, independent paraphrase set exists; do not manufacture one post-selection.
    if status == "EVALUATOR_DEV_PASSED":
        status = "EVALUATOR_DEV_MIXED"
    run_summary = {"status": status, "paraphrase_challenge": "PARAPHRASE_CHALLENGE_NOT_AVAILABLE", "three_word_marker_baseline": {"validation_balanced_accuracy": 0.8417, "test_balanced_accuracy": 0.7000, "source": "data/dataset_validity_audit.json"}, "final200_accessed_for_selection": False, "exp017_accessed_for_selection": False, "python_version": platform.python_version()}
    (RESULTS / "evaluator_development_summary.json").write_text(json.dumps(run_summary, indent=2) + "\n", encoding="utf-8")
    print("EVALUATOR_TRAINING_COMPLETE")
    print("validation_configs:", len(search_rows))
    print("selected:", json.dumps({key: selected[key] for key in ("word_ngram_range", "word_min_df", "char_ngram_range", "char_min_df", "C")}))
    print("procedural_test_status:", test_metrics["procedural_test_status"])
    print("lexical_challenge_status:", lexical_metrics["status"])
    print("evaluator_status:", status)


if __name__ == "__main__":
    main()
