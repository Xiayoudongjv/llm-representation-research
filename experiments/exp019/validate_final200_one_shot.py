"""Validate the frozen-input, one-shot EXP-019 Final-200 evaluation."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.behavioral_task_evaluator import CLASS_ORDER, SKLEARN_MODEL_CLASS_ORDER


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
RUNNER = EXP_DIR / "run_final200_one_shot.py"
EXPECTED_DATASET_HASH = "48E05DB992185661DF41C102C32CD4685944E50D0CD7454A195AB63C7B638765"
EXPECTED_ARTIFACT_HASH = "DF06E7683627F308330E77E8A50D35766F3CA50F5C8DE873E077092DEAEB2BDD"
EXPECTED_CONFIG_HASH = "EB673B63CB0C407C04F55F9B5F8FB687C7BD680FC5B53DDD4CC18A2BCC906744"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=1e-12)


def main() -> None:
    for path in (MANIFEST, PREDICTIONS, METRICS, PER_CLASS, CONFUSION, ERRORS):
        require(path.exists(), f"required one-shot result is absent: {path.name}")
    require(sha256(FROZEN) == EXPECTED_DATASET_HASH, "frozen dataset hash differs")
    require(sha256(ARTIFACT) == EXPECTED_ARTIFACT_HASH, "artifact hash differs")
    require(sha256(CONFIG) == EXPECTED_CONFIG_HASH, "config hash differs")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    require(tuple(config["class_order"]) == CLASS_ORDER and tuple(mapping["class_order"]) == CLASS_ORDER, "display class mapping is inconsistent")
    require(tuple(config["sklearn_model_class_order"]) == SKLEARN_MODEL_CLASS_ORDER, "sklearn class mapping is inconsistent")
    require(manifest == {**manifest, "dataset_sha256": EXPECTED_DATASET_HASH, "artifact_sha256": EXPECTED_ARTIFACT_HASH, "config_sha256": EXPECTED_CONFIG_HASH}, "run manifest hashes are inconsistent")
    require(manifest["dataset_size"] == 200 and manifest["class_counts"] == {label: 50 for label in CLASS_ORDER}, "run manifest dataset counts are inconsistent")
    require(manifest["one_shot"] is True and manifest["prediction_call_count"] == 1, "run manifest does not record exactly one prediction call")
    require(manifest["evaluator_refit"] is False and manifest["hyperparameters_modified"] is False and manifest["EXP017_accessed"] is False, "run manifest violates independence controls")
    runner_source = RUNNER.read_text(encoding="utf-8")
    require(".fit(" not in runner_source and ".fit_transform(" not in runner_source and ".partial_fit(" not in runner_source, "runner contains fitting code")

    frozen = read_csv(FROZEN)
    predictions = read_csv(PREDICTIONS)
    require(len(frozen) == 200 and len(predictions) == 200, "frozen/prediction row count is not 200")
    require([row["candidate_id"] for row in predictions] == [row["candidate_id"] for row in frozen], "prediction rows do not align to frozen rows")
    expected_columns = ["candidate_id", "true_task_class", "predicted_task_class", "p_logic", "p_causality", "p_analogy", "p_definition", "correct"]
    require(list(predictions[0]) == expected_columns, "prediction columns/order are inconsistent")
    truth, predicted = [], []
    for frozen_row, prediction in zip(frozen, predictions, strict=True):
        require(prediction["true_task_class"] == frozen_row["task_class"], "ground truth does not match frozen data")
        values = {label: float(prediction[f"p_{label}"]) for label in CLASS_ORDER}
        require(close(sum(values.values()), 1.0), "probabilities do not sum to one")
        expected_label = max(CLASS_ORDER, key=values.__getitem__)
        require(prediction["predicted_task_class"] == expected_label, "predicted class does not match frozen probability order")
        require((prediction["correct"].casefold() == "true") == (expected_label == frozen_row["task_class"]), "correct column is inconsistent")
        truth.append(frozen_row["task_class"])
        predicted.append(expected_label)
    require(Counter(truth) == Counter({label: 50 for label in CLASS_ORDER}), "frozen truth class counts are inconsistent")

    precision, recall, f1, support = precision_recall_fscore_support(truth, predicted, labels=CLASS_ORDER, zero_division=0)
    recomputed = {
        "balanced_accuracy": float(balanced_accuracy_score(truth, predicted)),
        "macro_f1": float(f1_score(truth, predicted, labels=CLASS_ORDER, average="macro", zero_division=0)),
        "accuracy": float(accuracy_score(truth, predicted)),
        "confusion_matrix": confusion_matrix(truth, predicted, labels=CLASS_ORDER).tolist(),
    }
    require(all(close(metrics[key], value) for key, value in recomputed.items() if key != "confusion_matrix"), "primary metrics do not reproduce")
    require(metrics["confusion_matrix"] == recomputed["confusion_matrix"], "confusion matrix does not reproduce")
    for index, label in enumerate(CLASS_ORDER):
        observed = metrics["per_class"][label]
        require(close(observed["precision"], float(precision[index])) and close(observed["recall"], float(recall[index])) and close(observed["f1"], float(f1[index])) and observed["support"] == int(support[index]), f"per-class metrics do not reproduce: {label}")
    accepted = recomputed["balanced_accuracy"] >= 0.70 and recomputed["macro_f1"] >= 0.70 and all(float(value) >= 0.60 for value in recall)
    expected_decision = "ACCEPTED_FOR_EXP017_TARGETNESS_EVALUATION" if accepted else "FAILED_INDEPENDENT_GENERALIZATION"
    require(metrics["acceptance_decision"] == expected_decision and metrics["exp017_targetness_unlocked"] is accepted, "acceptance decision does not match frozen thresholds")
    require(metrics["one_shot"] is True and metrics["evaluator_refit"] is False and metrics["hyperparameters_modified"] is False and metrics["EXP017_accessed"] is False, "metrics violate independence controls")
    errors = read_csv(ERRORS)
    require(len(errors) == sum(left != right for left, right in zip(truth, predicted, strict=True)), "error count does not match predictions")
    require(len(read_csv(PER_CLASS)) == 4 and len(read_csv(CONFUSION)) == 4, "metric CSV row count is inconsistent")
    print("FINAL200_ONE_SHOT_VALIDATION_PASS")
    print("prediction_rows: 200")
    print("acceptance_decision:", expected_decision)


if __name__ == "__main__":
    main()
