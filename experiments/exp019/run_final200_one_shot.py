"""Run the preregistered one-shot EXP-019 Final-200 evaluation.

This program only loads the persisted evaluator and calls ``predict_proba``
once on frozen response text. It never fits, transforms for fitting, retunes,
or accesses EXP-017.
"""

from __future__ import annotations

import csv
import hashlib
import json
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.behavioral_task_evaluator import CLASS_ORDER, SKLEARN_MODEL_CLASS_ORDER, load_evaluator, predict_proba


EXP_DIR = Path(__file__).resolve().parent
DATA = EXP_DIR / "data"
RESULTS = EXP_DIR / "results"
FROZEN = DATA / "final200_frozen.csv"
ARTIFACT = EXP_DIR / "artifacts" / "evaluator_tfidf_logreg.joblib"
CONFIG = EXP_DIR / "evaluator_frozen_config.json"
MAPPING = EXP_DIR / "artifacts" / "evaluator_label_mapping.json"
MANIFEST = RESULTS / "final200_one_shot_run_manifest.json"
PREDICTIONS = RESULTS / "final200_predictions.csv"
METRICS = RESULTS / "final200_metrics.json"
PER_CLASS = RESULTS / "final200_per_class_metrics.csv"
CONFUSION = RESULTS / "final200_confusion_matrix.csv"
ERRORS = RESULTS / "final200_errors.csv"
DOCUMENT = ROOT / "docs" / "experiments" / "EXP-019-FINAL200-ONE-SHOT-EVALUATION.md"
EXPECTED_DATASET_HASH = "48E05DB992185661DF41C102C32CD4685944E50D0CD7454A195AB63C7B638765"
EXPECTED_ARTIFACT_HASH = "DF06E7683627F308330E77E8A50D35766F3CA50F5C8DE873E077092DEAEB2BDD"
EXPECTED_CONFIG_HASH = "EB673B63CB0C407C04F55F9B5F8FB687C7BD680FC5B53DDD4CC18A2BCC906744"
ACCEPTANCE_BA = 0.70
ACCEPTANCE_F1 = 0.70
ACCEPTANCE_RECALL = 0.60


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def preflight(rows: list[dict[str, str]]) -> tuple[str, str, str, dict[str, int]]:
    dataset_hash, artifact_hash, config_hash = sha256(FROZEN), sha256(ARTIFACT), sha256(CONFIG)
    require(dataset_hash == EXPECTED_DATASET_HASH, "Frozen Final-200 hash differs from checkpoint.")
    require(artifact_hash == EXPECTED_ARTIFACT_HASH, "Evaluator artifact hash differs from checkpoint.")
    require(config_hash == EXPECTED_CONFIG_HASH, "Frozen config hash differs from checkpoint.")
    class_counts = dict(Counter(row["task_class"] for row in rows))
    require(len(rows) == 200 and class_counts == {label: 50 for label in CLASS_ORDER}, "Frozen Final-200 rows/classes differ from checkpoint.")
    require(len({row["candidate_id"] for row in rows}) == 200, "Frozen candidate IDs are not unique.")
    return dataset_hash, artifact_hash, config_hash, class_counts


def per_class_metrics(y_true: list[str], y_pred: list[str]) -> tuple[dict[str, dict[str, float | int]], list[list[int]]]:
    precision, recall, f1, support = precision_recall_fscore_support(y_true, y_pred, labels=CLASS_ORDER, zero_division=0)
    values = {
        label: {"precision": float(precision[index]), "recall": float(recall[index]), "f1": float(f1[index]), "support": int(support[index])}
        for index, label in enumerate(CLASS_ORDER)
    }
    return values, confusion_matrix(y_true, y_pred, labels=CLASS_ORDER).tolist()


def descriptive_group_metrics(rows: list[dict[str, str]], predictions: list[str], field: str) -> dict[str, dict[str, object]]:
    grouped: defaultdict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        grouped[row[field]].append(index)
    summary: dict[str, dict[str, object]] = {}
    for value, indices in sorted(grouped.items()):
        truth = [rows[index]["task_class"] for index in indices]
        predicted = [predictions[index] for index in indices]
        summary[value] = {
            "count": len(indices),
            "accuracy": float(accuracy_score(truth, predicted)),
            "balanced_accuracy": float(balanced_accuracy_score(truth, predicted)),
        }
    return summary


def document(metrics: dict[str, object]) -> str:
    per_class = metrics["per_class"]
    matrix = metrics["confusion_matrix"]
    recall_lines = "\n".join(f"- {label}: precision={per_class[label]['precision']:.4f}, recall={per_class[label]['recall']:.4f}, F1={per_class[label]['f1']:.4f}" for label in CLASS_ORDER)
    matrix_lines = "\n".join("| " + label + " | " + " | ".join(str(value) for value in matrix[index]) + " |" for index, label in enumerate(CLASS_ORDER))
    decision = metrics["acceptance_decision"]
    interpretation = (
        "The frozen evaluator achieved the preregistered minimum level of independent generalization on this Final-200 set. This does not establish semantic robustness beyond this frozen test set."
        if decision == "ACCEPTED_FOR_EXP017_TARGETNESS_EVALUATION"
        else "The substantial procedural-to-independent change indicates that procedural performance was likely inflated by lexical or template structure; the frozen evaluator did not meet the preregistered independent-generalization threshold."
    )
    unlock = "`EXP017_TARGETNESS_UNLOCKED = true`; no EXP-017 targetness analysis was run in this task." if decision == "ACCEPTED_FOR_EXP017_TARGETNESS_EVALUATION" else "EXP-017 remains `LOCKED` for targetness evaluation; no EXP-017 output was read."
    return f"""# EXP-019 Final-200 One-Shot Evaluation

## Frozen Inputs

Final-200, the persisted evaluator artifact, and frozen config were hash-verified before prediction. Dataset size was 200 with 50 rows per class.

## Independence Controls

Only `response_text` was supplied as evaluator input. No evaluator retraining occurred after freeze. No Final-200 example was modified after predictions were generated. Acceptance thresholds were frozen before evaluation.

## One-Shot Procedure

The persisted evaluator was loaded once, class/probability mapping was checked against the frozen config, and one `predict_proba` call generated all 200 predictions. No fitting, hyperparameter modification, or rerun occurred.

## Primary Metrics

- Balanced accuracy: {metrics['balanced_accuracy']:.4f}
- Macro F1: {metrics['macro_f1']:.4f}
- Accuracy: {metrics['accuracy']:.4f}

## Per-Class Metrics

{recall_lines}

## Confusion Matrix

Rows are true classes; columns are logic, causality, analogy, definition.

| true class | logic | causality | analogy | definition |
| --- | ---: | ---: | ---: | ---: |
{matrix_lines}

## Procedural vs Independent Performance

Procedural test balanced accuracy and macro F1 were both 1.0000. Independent Final-200 balanced accuracy was {metrics['balanced_accuracy']:.4f} and macro F1 was {metrics['macro_f1']:.4f}. Historical three-word-marker baselines were validation BA=0.8417 and procedural test BA=0.7000.

## Error Audit

There were {metrics['error_count']} misclassified rows. The error CSV is descriptive only and did not trigger repair or rerunning.

## Generalization Interpretation

{interpretation}

## Acceptance Decision

`{decision}`

## EXP-017 Unlock Decision

{unlock}

## Limitations

This is one frozen independent test set and an output-only TF-IDF/logistic-regression evaluator. Its result does not by itself establish semantic task understanding or behavioral steering effects.
"""


def main() -> None:
    RESULT_FILES = (MANIFEST, PREDICTIONS, METRICS, PER_CLASS, CONFUSION, ERRORS)
    require(not any(path.exists() for path in RESULT_FILES), "One-shot Final-200 result exists; refusing a second prediction run.")
    rows = read_csv(FROZEN)
    dataset_hash, artifact_hash, config_hash, class_counts = preflight(rows)
    RESULTS.mkdir(parents=True, exist_ok=True)
    manifest = {
        "dataset_sha256": dataset_hash,
        "artifact_sha256": artifact_hash,
        "config_sha256": config_hash,
        "dataset_size": 200,
        "class_counts": class_counts,
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "one_shot": True,
        "prediction_call_count": 0,
        "evaluator_refit": False,
        "hyperparameters_modified": False,
        "EXP017_accessed": False,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    require(tuple(config["class_order"]) == CLASS_ORDER, "Frozen display class order is inconsistent.")
    require(tuple(config["sklearn_model_class_order"]) == SKLEARN_MODEL_CLASS_ORDER, "Frozen sklearn class order is inconsistent.")
    require(tuple(mapping["class_order"]) == CLASS_ORDER, "Stored label mapping is inconsistent.")
    evaluator = load_evaluator(ARTIFACT)
    require(tuple(evaluator.classes_) == SKLEARN_MODEL_CLASS_ORDER, "Loaded evaluator class order is inconsistent.")

    response_texts = [row["response_text"] for row in rows]
    probability_rows = predict_proba(evaluator, response_texts)
    manifest["prediction_call_count"] = 1
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    predicted = [max(CLASS_ORDER, key=probability.__getitem__) for probability in probability_rows]
    truth = [row["task_class"] for row in rows]
    predictions = [{
        "candidate_id": row["candidate_id"],
        "true_task_class": row["task_class"],
        "predicted_task_class": predicted[index],
        "p_logic": probability_rows[index]["logic"],
        "p_causality": probability_rows[index]["causality"],
        "p_analogy": probability_rows[index]["analogy"],
        "p_definition": probability_rows[index]["definition"],
        "correct": predicted[index] == row["task_class"],
    } for index, row in enumerate(rows)]
    write_csv(PREDICTIONS, list(predictions[0]), predictions)

    per_class, matrix = per_class_metrics(truth, predicted)
    confidences = [max(probability.values()) for probability in probability_rows]
    correct_confidence = [confidences[index] for index, row in enumerate(predictions) if row["correct"]]
    incorrect_confidence = [confidences[index] for index, row in enumerate(predictions) if not row["correct"]]
    accepted = (
        balanced_accuracy_score(truth, predicted) >= ACCEPTANCE_BA
        and f1_score(truth, predicted, labels=CLASS_ORDER, average="macro", zero_division=0) >= ACCEPTANCE_F1
        and all(values["recall"] >= ACCEPTANCE_RECALL for values in per_class.values())
    )
    metrics: dict[str, object] = {
        "balanced_accuracy": float(balanced_accuracy_score(truth, predicted)),
        "macro_f1": float(f1_score(truth, predicted, labels=CLASS_ORDER, average="macro", zero_division=0)),
        "accuracy": float(accuracy_score(truth, predicted)),
        "per_class": per_class,
        "confusion_matrix": matrix,
        "acceptance_thresholds": {"balanced_accuracy_min": ACCEPTANCE_BA, "macro_f1_min": ACCEPTANCE_F1, "per_class_recall_min": ACCEPTANCE_RECALL},
        "acceptance_decision": "ACCEPTED_FOR_EXP017_TARGETNESS_EVALUATION" if accepted else "FAILED_INDEPENDENT_GENERALIZATION",
        "exp017_targetness_unlocked": bool(accepted),
        "error_count": len(incorrect_confidence),
        "confidence_summary": {
            "mean_max_probability": float(statistics.mean(confidences)),
            "median_max_probability": float(statistics.median(confidences)),
            "mean_max_probability_correct": float(statistics.mean(correct_confidence)) if correct_confidence else None,
            "mean_max_probability_incorrect": float(statistics.mean(incorrect_confidence)) if incorrect_confidence else None,
            "low_confidence_cases": [{"candidate_id": rows[index]["candidate_id"], "true_task_class": truth[index], "predicted_task_class": predicted[index], "max_probability": confidences[index]} for index in sorted(range(len(rows)), key=confidences.__getitem__)[:10]],
        },
        "descriptive_performance": {
            "task_class": descriptive_group_metrics(rows, predicted, "task_class"),
            "provenance": descriptive_group_metrics(rows, predicted, "provenance"),
            "topic_domain": descriptive_group_metrics(rows, predicted, "topic_domain"),
            "length_band": descriptive_group_metrics(rows, predicted, "length_band"),
        },
        "procedural_reference": {"balanced_accuracy": 1.0, "macro_f1": 1.0, "accuracy": 1.0, "three_word_marker_validation_balanced_accuracy": 0.8417, "three_word_marker_test_balanced_accuracy": 0.7000},
        "one_shot": True,
        "evaluator_refit": False,
        "hyperparameters_modified": False,
        "EXP017_accessed": False,
    }
    METRICS.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(PER_CLASS, ["task_class", "precision", "recall", "f1", "support"], [{"task_class": label, **per_class[label]} for label in CLASS_ORDER])
    write_csv(CONFUSION, ["true_task_class", *CLASS_ORDER], [{"true_task_class": label, **dict(zip(CLASS_ORDER, matrix[index], strict=True))} for index, label in enumerate(CLASS_ORDER)])
    errors = [{
        "candidate_id": rows[index]["candidate_id"],
        "true_task_class": truth[index],
        "predicted_task_class": predicted[index],
        "response_text": rows[index]["response_text"],
        "probabilities": json.dumps(probability_rows[index], ensure_ascii=False),
        "provenance": rows[index]["provenance"],
        "topic_domain": rows[index]["topic_domain"],
    } for index in range(len(rows)) if predicted[index] != truth[index]]
    write_csv(ERRORS, ["candidate_id", "true_task_class", "predicted_task_class", "response_text", "probabilities", "provenance", "topic_domain"], errors)
    DOCUMENT.write_text(document(metrics), encoding="utf-8")
    print("FINAL200_ONE_SHOT_EVALUATION_COMPLETE")
    print("prediction_rows:", len(predictions))
    print("acceptance_decision:", metrics["acceptance_decision"])


if __name__ == "__main__":
    main()
