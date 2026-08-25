#!/usr/bin/env python3
"""Validate the published PA-EXT-B V2 source-only production panel."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments" / "paper_a_ext_b"
DATA = BASE / "data"
STEPGAME = Path(r"D:\AI_Cache\huggingface\hub\datasets--ZhengyanShi--StepGame\snapshots\6d859381dfd518cae3f073b268aaa323bf4dcf04\train.jsonl")
WORDNET = ROOT / "experiments" / "paper_a_ext_a" / "data" / "raw" / "WordNet-3.0.tar.gz"
EXPECTED_STEPGAME_SHA = "774b73385c1a6995e121e87f16be790355555c4c18c01eb42464e28c6ea3482c"
EXPECTED_WORDNET_SHA = "640db279c949a88f61f851dd54ebbb22d003f8b90b85267042ef85a3781d3a52"
TASKS = [("TF_SPATIAL", "exta_tf_spatial", "spatial"), ("TF_QUANTITATIVE", "exta_tf_quantitative", "quantitative"), ("TF_MEREOLOGICAL", "exta_tf_mereological", "mereological")]
CONDITIONS = ["c01_lexical_relex", "c02_syntactic_restructure", "c03_controlled_compression", "c04_controlled_elaboration", "c05_relation_explicit", "c06_relation_implicit", "c07_register_formal", "c08_register_informal", "c09_neutral_distractor_prefix", "c10_anaphoric_reference"]
SPLITS = ["FIT", "DIAGNOSTIC", "EVAL"]
FORBIDDEN_KEY_PARTS = ("model_output", "hidden_state", "probability", "logit", "prediction", "scientific_result", "authorization")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_string(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = unicodedata.normalize("NFC", value)
    return re.sub(r"\s+", " ", value.strip()).casefold()


def surface_string(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = unicodedata.normalize("NFC", value)
    return re.sub(r"\s+", " ", value.strip())


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def family_id(slug: str, source_tuple: Any) -> str:
    payload = "PA-EXT-B-V1-FAMILY\0" + canonical_json(source_tuple)
    return "extb_sf_v2_" + slug + "_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def record_id(family: str, condition: str, role: str) -> str:
    payload = f"PA-EXT-B-V1-RECORD\0{family}\0{condition}\0{role}"
    return "extb_rec_v2_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _render(render: dict[str, Any], task: str, relation_key: str | None, arg_a: str, arg_b: str, condition_id: str, role: str) -> str:
    condition = next(item for item in render["conditions"] if item["condition_id"] == condition_id)
    fields = render["task_lexical_fields"][task]
    maps: dict[str, str] = {}
    for key in ("REL_LEX", "REL_LEX_ALT", "OVERT_REL", "IMPLICIT_REL"):
        value = fields[key]
        maps[key] = value if isinstance(value, str) else value[relation_key or "left"]
    if condition_id == "c03_controlled_compression":
        bare = render["c03_relation_lexicalization"][task]
        maps["REL_LEX"] = bare if isinstance(bare, str) else bare[relation_key or "left"]
    values = {**maps, "ARG_A": arg_a, "ARG_B": arg_b, "CONTEXT_PHRASE": render["bound_constants"]["CONTEXT_PHRASE"], "CONTEXT_PREFIX": render["bound_constants"]["CONTEXT_PREFIX"]}
    template = condition["reference_template"] if role == "reference" else condition["realization_template"]
    return surface_string(template.format(**values))


def _check_keys(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if any(fragment in key.lower() for fragment in FORBIDDEN_KEY_PARTS):
                errors.append(f"forbidden_key:{path}.{key}")
            _check_keys(child, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _check_keys(child, f"{path}[{index}]", errors)


def _validate_task(slug: str, label: str, task: dict[str, Any], bank: list[dict[str, Any]], render: dict[str, Any], errors: list[str]) -> list[dict[str, Any]]:
    if task.get("family_count") != 220 or task.get("record_count") != 440 or len(bank) != 220 or len(task.get("records", [])) != 440:
        errors.append(f"count:{slug}")
    if [row.get("selection_rank") for row in bank] != list(range(220)):
        errors.append(f"selection_order:{slug}")
    families = {row.get("source_family_id") for row in bank}
    if len(families) != 220:
        errors.append(f"family_unique:{slug}")
    expected_records: list[dict[str, Any]] = []
    for source in bank:
        family = family_id(slug, source.get("canonical_source_tuple"))
        if source.get("source_family_id") != family:
            errors.append(f"family_id:{slug}:{source.get('selection_rank')}")
        if source.get("selection_hash") != hashlib.sha256(("PA-EXT-B-V1-ORDER\0" + canonical_json(source.get("canonical_source_tuple"))).encode("utf-8")).hexdigest():
            errors.append(f"selection_hash:{slug}:{source.get('selection_rank')}")
        rank = int(source.get("selection_rank", -1))
        within = rank % 22 + 1
        split = "FIT" if within <= 6 else "DIAGNOSTIC" if within <= 14 else "EVAL"
        arg_a = surface_string(str(source.get("arg_a", "")).replace("_", " ") if slug == "mereological" else str(source.get("arg_a", "")))
        arg_b = surface_string(str(source.get("arg_b", "")).replace("_", " ") if slug == "mereological" else str(source.get("arg_b", "")))
        assigned_condition = CONDITIONS[rank // 22]
        for condition in (assigned_condition,):
            for role in ("reference", "realization"):
                expected_records.append({"family_id": family, "condition_id": condition, "record_role": role, "split": split, "record_id": record_id(family, condition, role), "rendered_text": _render(render, label, source.get("source_identity", {}).get("label") if slug == "spatial" else None, arg_a, arg_b, condition, role), "arg_a": arg_a, "arg_b": arg_b})
    actual = task.get("records", [])
    by_family: dict[str, list[dict[str, Any]]] = {}
    for row in actual:
        by_family.setdefault(str(row.get("family_id")), []).append(row)
    if len(by_family) != 220:
        errors.append(f"family_record_groups:{slug}")
    for family_name, rows in by_family.items():
        if len(rows) != 2:
            errors.append(f"records_per_family:{slug}:{family_name}")
            continue
        if len({row.get("condition_id") for row in rows}) != 1:
            errors.append(f"multiple_conditions_per_family:{slug}:{family_name}")
        if {row.get("record_role") for row in rows} != {"reference", "realization"}:
            errors.append(f"record_roles:{slug}:{family_name}")
        for key in ("task_slug", "split", "semantic_relation", "source_identity", "arg_a", "arg_b"):
            if len({canonical_json(row.get(key)) for row in rows}) != 1:
                errors.append(f"paired_field_mismatch:{slug}:{family_name}:{key}")
    family_counts: dict[tuple[str, str], set[str]] = {}
    for row in actual:
        family_counts.setdefault((str(row.get("split")), str(row.get("condition_id"))), set()).add(str(row.get("family_id")))
    for split_name, expected_per_condition in (("FIT", 6), ("DIAGNOSTIC", 8), ("EVAL", 8)):
        for condition in CONDITIONS:
            if len(family_counts.get((split_name, condition), set())) != expected_per_condition:
                errors.append(f"split_condition_count:{slug}:{split_name}:{condition}")
    if len(actual) == len(expected_records):
        expected_records.sort(key=lambda row: (SPLITS.index(row["split"]), CONDITIONS.index(row["condition_id"]), row["family_id"], row["record_role"]))
        for index, (got, want) in enumerate(zip(actual, expected_records)):
            for key in ("family_id", "condition_id", "record_role", "split", "record_id", "rendered_text", "arg_a", "arg_b"):
                if got.get(key) != want[key]:
                    errors.append(f"record:{slug}:{index}:{key}")
                    break
            if got.get("label") != label or got.get("task_slug") != slug:
                errors.append(f"record_identity:{slug}:{index}")
    return actual


def validate() -> list[str]:
    errors: list[str] = []
    expected_files = ["tf_spatial_source_bank.json", "tf_spatial_dataset.json", "tf_quantitative_source_bank.json", "tf_quantitative_dataset.json", "tf_mereological_source_bank.json", "tf_mereological_dataset.json", "ext_b_frozen_panel.json", "ext_b_panel_manifest.json", "ext_b_construction_provenance.json", "ext_b_freeze_binding.json"]
    for name in expected_files:
        if not (DATA / name).is_file():
            errors.append(f"missing:{name}")
    if errors:
        return errors
    if sha256(STEPGAME) != EXPECTED_STEPGAME_SHA or sha256(WORDNET) != EXPECTED_WORDNET_SHA:
        errors.append("source_identity")
    render = _json(BASE / "paper_a_ext_b_rendering_conditions_c01_c10_v2.json")
    all_records: list[dict[str, Any]] = []
    for label, task_id, slug in TASKS:
        bank = _json(DATA / f"tf_{slug}_source_bank.json")
        task = _json(DATA / f"tf_{slug}_dataset.json")
        if not isinstance(bank, list) or task.get("source_families") != bank:
            errors.append(f"bank_binding:{slug}")
            bank = bank if isinstance(bank, list) else []
        if task.get("task_id") != task_id:
            errors.append(f"task_id:{slug}")
        all_records.extend(_validate_task(slug, label, task, bank, render, errors))
    if len(all_records) != 1320:
        errors.append("combined_record_count")
    exact = [row.get("rendered_text") for row in all_records]
    normalized = [canonical_string(str(text)) for text in exact]
    if len(set(exact)) != len(exact):
        errors.append("exact_duplicate")
    if len(set(normalized)) != len(normalized):
        errors.append("normalized_duplicate")
    panel = _json(DATA / "ext_b_frozen_panel.json")
    if panel.get("records") != all_records or panel.get("family_count") != 660 or panel.get("record_count") != 1320:
        errors.append("panel_binding")
    if panel.get("model_inference_performed") is not False or panel.get("scientific_result_created") is not False:
        errors.append("panel_outcome_state")
    manifest = _json(DATA / "ext_b_panel_manifest.json")
    for slug in ("spatial", "quantitative", "mereological"):
        if manifest.get("source_bank_hashes", {}).get(slug) != sha256(DATA / f"tf_{slug}_source_bank.json"):
            errors.append(f"manifest_bank_hash:{slug}")
        if manifest.get("task_dataset_hashes", {}).get(slug) != sha256(DATA / f"tf_{slug}_dataset.json"):
            errors.append(f"manifest_task_hash:{slug}")
    if manifest.get("combined_panel_sha256") != sha256(DATA / "ext_b_frozen_panel.json"):
        errors.append("manifest_panel_hash")
    if manifest.get("family_counts", {}).get("total") != 660 or manifest.get("record_counts", {}).get("total") != 1320:
        errors.append("manifest_counts")
    if manifest.get("model_inference_performed") is not False or manifest.get("scientific_result_created") is not False:
        errors.append("manifest_outcome_state")
    provenance = _json(DATA / "ext_b_construction_provenance.json")
    if provenance.get("three_of_three_gate_state") != {"SPATIAL_READY": True, "QUANTITATIVE_READY": True, "MEREOLOGICAL_READY": True, "EXT_B_3_OF_3_DATASET_GATE_PASS": True}:
        errors.append("three_of_three_gate")
    if provenance.get("input_source_identities", {}).get("stepgame_train", {}).get("sha256") != EXPECTED_STEPGAME_SHA or provenance.get("input_source_identities", {}).get("wordnet_3_0", {}).get("sha256") != EXPECTED_WORDNET_SHA:
        errors.append("provenance_source_hash")
    if provenance.get("canonical_hashes", {}).get("experiments/paper_a_ext_b/data/ext_b_frozen_panel.json") != sha256(DATA / "ext_b_frozen_panel.json"):
        errors.append("provenance_panel_hash")
    if provenance.get("generation_identity", {}).get("builder_path") != "experiments/paper_a_ext_b/build_paper_a_ext_b_dataset_v2.py":
        errors.append("provenance_builder")
    binding = _json(DATA / "ext_b_freeze_binding.json")
    if binding.get("production_artifact_hashes", {}).get("experiments/paper_a_ext_b/data/ext_b_frozen_panel.json") != sha256(DATA / "ext_b_frozen_panel.json"):
        errors.append("binding_panel_hash")
    for value in (panel, manifest, provenance, binding):
        _check_keys(value, "artifact", errors)
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        print("EXT_B_V2_DATASET_VALIDATION=FAIL")
        print("\n".join(sorted(set(failures))))
        raise SystemExit(1)
    print("EXT_B_V2_DATASET_VALIDATION=PASS")
    print("SPATIAL_READY=true")
    print("QUANTITATIVE_READY=true")
    print("MEREOLOGICAL_READY=true")
    print("EXT_B_3_OF_3_DATASET_GATE_PASS=true")
    print("MODEL_INFERENCE_RUN=false")
