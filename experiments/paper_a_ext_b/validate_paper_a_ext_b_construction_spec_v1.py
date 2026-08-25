#!/usr/bin/env python3
"""Static, no-data qualification of the EXT-B pre-generation construction spec."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments" / "paper_a_ext_b"
SPEC_PATH = BASE / "paper_a_ext_b_construction_spec_v1.json"
RENDER_PATH = BASE / "paper_a_ext_b_rendering_conditions_c01_c10_v1.json"
AMEND_PATH = BASE / "paper_a_ext_b_construction_amendment_v1.json"

EXPECTED_PARENT = "640ef4cca8c012491c81eed32215b2abfbe7f07e"
PARENT_HASHES = {
    "docs/experiments/PAPER-A-EXT-B-PREREGISTRATION.md": "4e25dd8e9bbaf4ac6a3240ddc9f96b01532ed20591e2e1527a4448db8ebd5184",
    "experiments/paper_a_ext_b/paper_a_ext_b_preregistration.json": "8069439f96db96649a7bbbff3413b2ec6dda37a72d5bbb98a72934349c3e42f8",
    "experiments/paper_a_ext_b/paper_a_ext_b_frozen_protocol.json": "c67e8786f93d593dfd8ae70c1e1348758997baf097aed4e5393a4e30641a40ac",
    "experiments/paper_a_ext_b/paper_a_ext_b_outcome_routing.json": "6e0ad230664e10b26849ef284fae11174093d2adf4d36eb79dc37201ab29e7f0",
    "experiments/paper_a_ext_b/paper_a_ext_b_authority_manifest.json": "63a03e1d3b8aacc6858ea880f7a29b778d064882738075ea1287c6ef0b23f39c",
}
CONDITIONS = [
    "c01_lexical_relex", "c02_syntactic_restructure",
    "c03_controlled_compression", "c04_controlled_elaboration",
    "c05_relation_explicit", "c06_relation_implicit",
    "c07_register_formal", "c08_register_informal",
    "c09_neutral_distractor_prefix", "c10_anaphoric_reference",
]
SPATIAL_LABELS = [
    "above", "below", "left", "lower-left", "lower-right", "overlap",
    "right", "upper-left", "upper-right",
]
WORDNET_TYPES = [
    "part_meronym", "member_meronym", "substance_meronym",
    "part_holonym", "member_holonym", "substance_holonym",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_string(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = unicodedata.normalize("NFC", value)
    return re.sub(r"\s+", " ", value.strip()).casefold()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def family_id(task_slug: str, source_tuple: Any) -> str:
    payload = canonical_json(source_tuple)
    digest = hashlib.sha256(("PA-EXT-B-V1-FAMILY\0" + payload).encode("utf-8")).hexdigest()
    return f"extb_sf_v1_{task_slug}_{digest}"


def record_id(family: str, condition: str, role: str) -> str:
    payload = f"PA-EXT-B-V1-RECORD\0{family}\0{condition}\0{role}"
    return "extb_rec_v1_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_spec() -> list[str]:
    errors: list[str] = []
    for path in [SPEC_PATH, RENDER_PATH, AMEND_PATH]:
        if not path.exists():
            errors.append(f"missing:{path}")
    if errors:
        return errors
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    render = json.loads(RENDER_PATH.read_text(encoding="utf-8"))
    amend = json.loads(AMEND_PATH.read_text(encoding="utf-8"))

    if amend["parent_commit"] != EXPECTED_PARENT:
        errors.append("parent_commit_mismatch")
    if amend["generated_records_before_amendment"] != 0:
        errors.append("pre_amendment_records_nonzero")
    if amend["model_outcome_observed_before_amendment"]:
        errors.append("pre_amendment_model_outcome_true")
    if amend["scientific_result_observed_before_amendment"]:
        errors.append("pre_amendment_result_true")
    if spec["selection_and_split_order"]["families_per_condition"] != 22:
        errors.append("families_per_condition_mismatch")
    if spec["frozen_counts"] != {"families_per_task": 220, "records_per_task": 440, "total_families": 660, "total_records": 1320}:
        errors.append("count_contract_mismatch")
    if spec["conditions_and_record_contract"]["condition_ids"] != CONDITIONS:
        errors.append("condition_contract_mismatch")
    if render["conditions"] and [item["condition_id"] for item in render["conditions"]] != CONDITIONS:
        errors.append("render_condition_order_mismatch")
    if spec["spatial"]["allowed_relation_labels"] != SPATIAL_LABELS:
        errors.append("spatial_label_contract_mismatch")
    if spec["mereological"]["allowed_relation_types"] != WORDNET_TYPES:
        errors.append("wordnet_relation_contract_mismatch")
    quant = spec["quantitative"]
    if quant["numeric_a"] != "10 + within_condition_index" or quant["numeric_b"] != "5 - within_condition_index":
        errors.append("quantitative_formula_mismatch")
    if quant["comparison_relation"] != "ARG_A > ARG_B" or quant["equality"] != "excluded by construction; equality is not an eligible source relation":
        errors.append("quantitative_comparison_contract_mismatch")
    if "xa01_" in json.dumps(render) or "xa02_" in json.dumps(render):
        errors.append("legacy_condition_id_emitted")
    if not spec["shared_identity"]["hash_algorithm"].startswith("SHA-256"):
        errors.append("identity_hash_algorithm_missing")
    if spec["shared_identity"]["timestamps_and_random_uuid"]:
        errors.append("nondeterministic_identity_allowed")
    if spec["validator_contract"]["production_data_generation"]:
        errors.append("validator_generation_enabled")
    for relative, expected in PARENT_HASHES.items():
        path = ROOT / relative
        if not path.exists() or sha256(path) != expected:
            errors.append(f"parent_hash_mismatch:{relative}")

    synthetic_family = family_id("spatial", ["exta_tf_spatial", "rev", 1, "left"])
    if synthetic_family != family_id("spatial", ["exta_tf_spatial", "rev", 1, "left"]):
        errors.append("family_id_not_repeatable")
    synthetic_record = record_id(synthetic_family, CONDITIONS[0], "reference")
    if synthetic_record != record_id(synthetic_family, CONDITIONS[0], "reference"):
        errors.append("record_id_not_repeatable")
    if synthetic_record == record_id(synthetic_family, CONDITIONS[0], "realization"):
        errors.append("record_role_not_bound")
    return errors


def main() -> int:
    errors = validate_spec()
    if errors:
        print("EXT_B_CONSTRUCTION_SPEC_VALIDATION=FAIL")
        for error in errors:
            print(error)
        return 1
    print("EXT_B_CONSTRUCTION_SPEC_VALIDATION=PASS")
    print("DATA_GENERATION_PERFORMED=false")
    print("MODEL_INFERENCE_PERFORMED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
