#!/usr/bin/env python3
"""Deterministic validator for the frozen EXP-024 authorities.

This validator checks file identities, frozen protocol fields, dataset counts,
and absence of formal scientific outcomes. It does not import or load any model,
tokenizer, or representation code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_MANIFEST = os.path.join(ROOT, "experiments", "exp024", "exp024_frozen_manifest.json")

EXPECTED_MODEL_REVISION = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
EXPECTED_PERMUTATION_COUNT = 3628800
EXPECTED_SUPPORT_RULE = "rho>0_and_p<=0.05"

RESULT_CANDIDATES = [
    os.path.join(ROOT, "experiments", "exp024", "results", "exp024_formal_result.json"),
    os.path.join(ROOT, "experiments", "exp024", "data", "exp024_formal_result.json"),
    os.path.join(ROOT, "experiments", "exp024", "exp024_formal_result.json"),
]

FORBIDDEN_PREREGISTRATION_TOKENS = [
    "TBD",
    "TODO",
    "PLACEHOLDER",
    "DRAFT_NOT_FROZEN",
    "ACTIVE_PROSPECTIVE_NOT_TESTED",
    "PROTOCOL_DRAFTED_NOT_FROZEN",
    "FORMAL_DATASET_CREATED = false",
    "EXP024_PREREGISTRATION_FROZEN = false",
]


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def path_from_manifest(manifest: dict, key: str) -> str:
    value = manifest.get(key)
    if not isinstance(value, str):
        raise ValueError(f"Manifest field {key!r} is missing or not a string.")
    return os.path.join(ROOT, value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate frozen EXP-024 authorities.")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    errors: list[str] = []

    if not os.path.exists(args.manifest):
        print("EXP024_FREEZE_VALIDATION = FAIL")
        print(f"ERROR: manifest not found: {args.manifest}")
        return 1

    try:
        with open(args.manifest, "r", encoding="utf-8") as handle:
            manifest = json.load(handle)
    except Exception as exc:
        print("EXP024_FREEZE_VALIDATION = FAIL")
        print(f"ERROR: manifest does not parse: {exc}")
        return 1

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    # Frozen dataset identity and byte identity to the reviewed candidate.
    dataset_path = path_from_manifest(manifest, "frozen_dataset_path")
    require(os.path.exists(dataset_path), f"Frozen dataset does not exist: {dataset_path}")
    if os.path.exists(dataset_path):
        actual_dataset_hash = sha256_file(dataset_path)
        require(actual_dataset_hash == manifest.get("frozen_dataset_sha256"), "Frozen dataset SHA mismatch with manifest.")
        require(actual_dataset_hash == manifest.get("source_candidate_sha256"), "Frozen dataset does not match source reviewed candidate identity.")

        try:
            with open(dataset_path, "r", encoding="utf-8") as handle:
                records = json.load(handle)
        except Exception as exc:
            records = None
            errors.append(f"Frozen dataset does not parse: {exc}")

        if records is not None:
            family_ids = {record.get("source_family_id") for record in records}
            condition_ids = {record.get("condition_id") for record in records}
            class_ids = {record.get("semantic_class") for record in records}
            partition_counts = Counter(record.get("partition") for record in records)
            require(len(records) == 1760, f"Expected 1760 records, found {len(records)}.")
            require(len(family_ids) == 880, f"Expected 880 source families, found {len(family_ids)}.")
            require(len(condition_ids) == 10, f"Expected 10 conditions, found {len(condition_ids)}.")
            require(len(class_ids) == 4, f"Expected 4 semantic classes, found {len(class_ids)}.")
            require(partition_counts["FIT"] // 2 == 240, "FIT family count mismatch.")
            require(partition_counts["DIAGNOSTIC"] // 2 == 320, "DIAGNOSTIC family count mismatch.")
            require(partition_counts["EVAL"] // 2 == 320, "EVAL family count mismatch.")
            require(manifest.get("primary_scientific_unit") == "condition", "Primary scientific unit is not condition.")
            require(manifest.get("n_conditions") == 10, "Manifest condition count is not 10.")

    # Final preregistration identity and protocol content.
    prereg_path = path_from_manifest(manifest, "final_preregistration_path")
    require(os.path.exists(prereg_path), f"Final preregistration does not exist: {prereg_path}")
    if os.path.exists(prereg_path):
        actual_prereg_hash = sha256_file(prereg_path)
        require(actual_prereg_hash == manifest.get("final_preregistration_sha256"), "Final preregistration SHA mismatch with manifest.")
        try:
            with open(prereg_path, "r", encoding="utf-8") as handle:
                prereg_text = handle.read()
        except Exception as exc:
            prereg_text = ""
            errors.append(f"Final preregistration cannot be read: {exc}")

        require("FROZEN_NOT_RUN" in prereg_text, "Final preregistration does not record FROZEN_NOT_RUN.")
        require("EXP024_PREREGISTRATION_FROZEN = true" in prereg_text, "Final preregistration is not marked frozen.")
        require("S_diag(c)" in prereg_text, "Primary diagnostic formula identity missing.")
        require("BA_A0(block16_pre_final_rmsnorm, DIAG_c)" in prereg_text, "S_diag block16 term missing.")
        require("BA_A0(block27_pre_final_rmsnorm, DIAG_c)" in prereg_text, "S_diag block27 term missing.")
        require("G_eval(c)" in prereg_text, "Primary outcome formula identity missing.")
        require("BA_A_mu_sigma(block27_pre_final_rmsnorm, EVAL_c)" in prereg_text, "G_eval A_mu_sigma term missing.")
        require("BA_A0(block27_pre_final_rmsnorm, EVAL_c)" in prereg_text, "G_eval A0 term missing.")
        require("Spearman" in prereg_text, "Primary statistic is not Spearman.")
        require("one-sided exact" in prereg_text or "one-sided exact condition-level permutation" in prereg_text, "Exact one-sided permutation test missing.")
        require(
            str(EXPECTED_PERMUTATION_COUNT) in prereg_text or f"{EXPECTED_PERMUTATION_COUNT:,}" in prereg_text,
            "Exact permutation count 3628800 missing.",
        )
        require("rho_primary > 0" in prereg_text, "Primary support rule rho > 0 missing.")
        require("exact_one_sided_p <= 0.05" in prereg_text, "Primary support rule p <= 0.05 missing.")
        require(EXPECTED_MODEL_REVISION in prereg_text, "Frozen model revision missing.")
        for token in FORBIDDEN_PREREGISTRATION_TOKENS:
            require(token not in prereg_text, f"Forbidden placeholder/draft token remains in preregistration: {token}")

    # Condition panel and schema identities.
    for path_key, label in [
        ("condition_panel_path", "Condition panel"),
        ("data_schema_path", "Data schema"),
        ("candidate_validator_path", "Candidate validator"),
        ("repair_log_path", "Repair log"),
        ("r2_review_markdown_path", "R2 Markdown review"),
        ("r2_review_json_path", "R2 structured review"),
    ]:
        path = path_from_manifest(manifest, path_key)
        hash_key = path_key.replace("_path", "_sha256")
        require(os.path.exists(path), f"{label} does not exist: {path}")
        if os.path.exists(path):
            require(sha256_file(path) == manifest.get(hash_key), f"{label} SHA mismatch with manifest.")

    # Validator identity is recorded in the manifest and matches this file.
    validator_path = os.path.abspath(__file__)
    actual_validator_hash = sha256_file(validator_path)
    require(actual_validator_hash == manifest.get("freeze_validator_sha256"), "Freeze validator identity is not recorded correctly in the manifest.")

    # Frozen analysis fields in manifest.
    require(manifest.get("freeze_status") == "FROZEN_NOT_RUN", "Manifest freeze status is not FROZEN_NOT_RUN.")
    require(manifest.get("primary_diagnostic_formula_identity") == "S_diag(c)", "Manifest primary diagnostic identity mismatch.")
    require(manifest.get("primary_outcome_formula_identity") == "G_eval(c)", "Manifest primary outcome identity mismatch.")
    require(manifest.get("primary_statistic") == "Spearman_rho", "Manifest primary statistic mismatch.")
    require(manifest.get("primary_test") == "exact_one_sided_condition_permutation", "Manifest primary test mismatch.")
    require(manifest.get("permutation_count") == EXPECTED_PERMUTATION_COUNT, "Manifest permutation count mismatch.")
    require(manifest.get("support_rule") == EXPECTED_SUPPORT_RULE, "Manifest support rule mismatch.")
    require(manifest.get("model_revision") == EXPECTED_MODEL_REVISION, "Manifest model revision mismatch.")
    require(manifest.get("model_access_performed") is False, "Manifest model-access flag must be false.")
    require(manifest.get("scientific_outcome_observed") is False, "Manifest scientific-outcome flag must be false.")

    # No formal result path may exist.
    for result_path in RESULT_CANDIDATES:
        require(not os.path.exists(result_path), f"Formal result path unexpectedly exists: {result_path}")

    if errors:
        print("EXP024_FREEZE_VALIDATION = FAIL")
        for error in errors:
            print("ERROR:", error)
        return 1

    print("EXP024_FREEZE_VALIDATION = PASS")
    print("FROZEN_DATASET_BYTE_IDENTITY = PASS")
    print("PREREGISTRATION_FROZEN_NOT_RUN = PASS")
    print("MODEL_ACCESS_PERFORMED = false")
    print("SCIENTIFIC_OUTCOME_OBSERVED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
