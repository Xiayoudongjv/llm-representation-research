"""Validate frozen next-phase protocols and hardware-qualification boundaries."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXP_DIR = Path(__file__).resolve().parent
RESULT = EXP_DIR / "results" / "hardware_qualification.json"
DOCS = [
    ROOT / "docs" / "experiments" / "NEXT-PHASE-PREREGISTRATION.md",
    ROOT / "docs" / "experiments" / "EXP-020-PREREGISTRATION.md",
    ROOT / "docs" / "experiments" / "EXP-021-PREREGISTRATION.md",
]
RUNNER = EXP_DIR / "hardware_qualification.py"
FORBIDDEN_FORMAL_OUTPUTS = ("transition_metrics.csv", "probe_metrics.csv", "invariant_metrics.csv", "representation_summary.json", "behavioral_outputs.csv")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    require(all(path.exists() for path in DOCS), "required preregistration document is absent")
    combined = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for phrase in ("Qwen/Qwen3-4B", "FIT", "EVAL", "MATCHED_RANDOM", "OPPOSITE", "0.50", "0.75", "beta 0.75", "REPRESENTATION_REPLICATION_SUPPORTED", "BEHAVIOR_NOT_RUN_BY_PREREGISTERED_STOP_RULE", "CONDITIONAL_FOLLOWUP"):
        require(phrase in combined, f"frozen protocol phrase missing: {phrase}")
    require(RESULT.exists(), "hardware qualification record is absent")
    record = json.loads(RESULT.read_text(encoding="utf-8"))
    require(record["formal_exp020_results_created"] is False and record["exp017_accessed"] is False, "qualification crossed a scientific boundary")
    requested_model = record.get("requested_model_id") or record.get("model_metadata", {}).get("model_id")
    require(requested_model == "Qwen/Qwen3-4B", "wrong model qualified")
    require(record["mode_order"] == ["MODE_A_NATIVE", "MODE_B_CPU_OFFLOAD", "MODE_C_4BIT"], "mode order changed")
    require(record["qualification_status"] in {"QUALIFIED", "HARDWARE_INFEASIBLE"}, "invalid qualification status")
    if record["qualification_status"] == "QUALIFIED":
        selected = record["selected_mode"]
        require(selected["hidden_state_extraction_success"] is True and selected["short_generation_success"] is True and selected["selected_block_hooks_accessible"] is True, "selected mode did not complete diagnostics")
        require(selected["selected_layers"]["primary_depth_0_50"] >= 0 and selected["selected_layers"]["secondary_depth_0_75"] >= 0, "normalized depth mapping absent")
    else:
        require(record.get("attempts") == [], "an access-blocked qualification must not attempt a loading mode")
        require(bool(record.get("access_error", {}).get("error")), "hardware-infeasible result lacks the access error")
        require(record.get("hardware_feasibility") == "UNTESTED", "access failure must not be labeled as a hardware test")
        require(record.get("model_access_status") == "BLOCKED", "access failure must record blocked model access")
        require(record.get("qualification_stage_reached") == "BEFORE_MODEL_CONFIG_LOAD", "access failure stage is inaccurate")
        require(record.get("cache_configuration", {}).get("planned_download_cache_dir") == r"D:\AI_Cache\huggingface", "planned cache location changed")
        require(record.get("network_diagnostic_classification") == "GENERAL_NETWORK_BLOCK", "network failure classification is missing")
    source = RUNNER.read_text(encoding="utf-8")
    require("neutral hardware diagnostic" in source.casefold(), "neutral diagnostic text missing")
    require("exp017" in source.casefold() and "formal" in source.casefold(), "boundary guard language missing")
    results_dir = EXP_DIR / "results"
    require(not any((results_dir / name).exists() for name in FORBIDDEN_FORMAL_OUTPUTS), "formal EXP-020 outcome file exists")
    print("NEXT_PHASE_PREREGISTRATION_VALIDATION_PASS")
    print("qualification_status:", record["qualification_status"])
    print("frozen_execution_mode:", record.get("frozen_execution_mode"))


if __name__ == "__main__":
    main()
