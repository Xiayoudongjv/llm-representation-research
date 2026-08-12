"""Validate the frozen EXP-019 evaluator development artifacts offline."""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.behavioral_task_evaluator import CLASS_ORDER, load_evaluator, predict_proba, predict_task


EXP_DIR = Path(__file__).resolve().parent
DATA = EXP_DIR / "data" / "behavioral_targetness_dataset.csv"
RESULTS = EXP_DIR / "results"
ARTIFACT = EXP_DIR / "artifacts" / "evaluator_tfidf_logreg.joblib"
LABELS = EXP_DIR / "artifacts" / "evaluator_label_mapping.json"
CONFIG = EXP_DIR / "evaluator_frozen_config.json"
TRAINER = EXP_DIR / "train_behavioral_task_evaluator.py"
FORBIDDEN_PATHS = ("final200_pre_human_audit_locked.csv", "final200_frozen.csv", "results/exp017", "experiments/exp017")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    test = json.loads((RESULTS / "evaluator_procedural_test_metrics.json").read_text(encoding="utf-8"))
    challenge = json.loads((RESULTS / "evaluator_lexical_challenge_metrics.json").read_text(encoding="utf-8"))
    summary = json.loads((RESULTS / "evaluator_development_summary.json").read_text(encoding="utf-8"))
    search = read_csv(RESULTS / "evaluator_validation_search.csv")
    classes = json.loads(LABELS.read_text(encoding="utf-8"))
    per_class = read_csv(RESULTS / "evaluator_per_class_metrics.csv")
    confusion = read_csv(RESULTS / "evaluator_confusion_matrix.csv")
    feature_audit = read_csv(RESULTS / "evaluator_feature_audit.csv")
    source = TRAINER.read_text(encoding="utf-8")

    require(len(search) == 80, f"expected 80 validation configurations, found {len(search)}")
    require(set(row["selection_data"] for row in search) == {"validation_only"}, "non-validation selection record")
    require(config["class_order"] == list(CLASS_ORDER), "fixed output class order mismatch")
    require(classes["class_order"] == list(CLASS_ORDER), "label mapping mismatch")
    require(config["final200_accessed_for_selection"] is False and config["exp017_accessed_for_selection"] is False, "forbidden selection access flag")
    require(test["final200_accessed"] is False and test["exp017_accessed"] is False, "forbidden test access flag")
    require(len(per_class) == 4 and len(confusion) == 4 and len(feature_audit) == 80, "expected metric report dimensions missing")
    require(config["test_evaluated_at_selection"] is False, "test was used at selection")
    require(datetime.fromisoformat(config["timestamp_utc"]) <= datetime.fromisoformat(test["evaluation_timestamp_utc"]), "config was not frozen before test timestamp")
    require(all(path.split("/")[-1] in source or path.split("\\")[-1] in source for path in FORBIDDEN_PATHS), "forbidden path list incomplete")
    require("final200" not in str(DATA).casefold(), "non-procedural corpus path selected")
    require(challenge["frozen_subset"] == "dataset lexical_challenge=true AND split=test", "lexical subset changed")

    model = load_evaluator(ARTIFACT)
    procedural_sample = [row for row in read_csv(DATA) if row["split"] == "train"][:4]
    texts = [row["response_text"] for row in procedural_sample]
    first = predict_proba(model, texts)
    second = predict_proba(load_evaluator(ARTIFACT), texts)
    require(first == second, "reload changed probabilities")
    require(predict_task(model, texts) == predict_task(load_evaluator(ARTIFACT), texts), "reload changed predicted classes")
    require(all(tuple(item) == CLASS_ORDER for item in first), "probability output order not fixed")

    print("EVALUATOR_DEVELOPMENT_VALIDATION_PASS")
    print("procedural_corpus:", DATA.name)
    print("validation_configurations:", len(search))
    print("class_order:", ",".join(CLASS_ORDER))
    print("artifact_reload_reproducible: true")
    print("final200_accessed_for_selection: false")
    print("exp017_accessed: false")
    print("post_test_retuning_record: absent")
    print("development_status:", summary["status"])


if __name__ == "__main__":
    main()
