#!/usr/bin/env python3
"""Build the single, frozen PA-EXT-B V2 three-task panel.

This is a source-only constructor.  It never imports a model library and it
publishes the complete data directory only after all in-memory checks pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import tarfile
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments" / "paper_a_ext_b"
DATA = BASE / "data"
STEPGAME = Path(r"D:\AI_Cache\huggingface\hub\datasets--ZhengyanShi--StepGame\snapshots\6d859381dfd518cae3f073b268aaa323bf4dcf04\train.jsonl")
WORDNET = ROOT / "experiments" / "paper_a_ext_a" / "data" / "raw" / "WordNet-3.0.tar.gz"
BUILDER_REL = "experiments/paper_a_ext_b/build_paper_a_ext_b_dataset_v2.py"
VALIDATOR_REL = "experiments/paper_a_ext_b/validate_paper_a_ext_b_dataset_v2.py"
STATIC_VALIDATOR_REL = "experiments/paper_a_ext_b/validate_paper_a_ext_b_construction_v2.py"

EXPECTED_STEPGAME_SHA = "774b73385c1a6995e121e87f16be790355555c4c18c01eb42464e28c6ea3482c"
EXPECTED_WORDNET_SHA = "640db279c949a88f61f851dd54ebbb22d003f8b90b85267042ef85a3781d3a52"
V2_SPEC = BASE / "paper_a_ext_b_construction_spec_v2.json"
V2_RENDER = BASE / "paper_a_ext_b_rendering_conditions_c01_c10_v2.json"
V2_AMENDMENT = BASE / "paper_a_ext_b_construction_amendment_v2.json"
V2_SOURCE_SCHEMA = BASE / "paper_a_ext_b_source_bank_schema_v2.json"
V2_RECORD_SCHEMA = BASE / "paper_a_ext_b_record_schema_v2.json"
V2_PANEL_SCHEMA = BASE / "paper_a_ext_b_panel_manifest_schema_v2.json"
V2_PROVENANCE_SCHEMA = BASE / "paper_a_ext_b_provenance_schema_v2.json"

TASKS = [
    ("TF_SPATIAL", "exta_tf_spatial", "spatial"),
    ("TF_QUANTITATIVE", "exta_tf_quantitative", "quantitative"),
    ("TF_MEREOLOGICAL", "exta_tf_mereological", "mereological"),
]
CONDITIONS = [
    "c01_lexical_relex", "c02_syntactic_restructure", "c03_controlled_compression",
    "c04_controlled_elaboration", "c05_relation_explicit", "c06_relation_implicit",
    "c07_register_formal", "c08_register_informal", "c09_neutral_distractor_prefix",
    "c10_anaphoric_reference",
]
SPATIAL_LABELS = {"above", "below", "left", "lower-left", "lower-right", "overlap", "right", "upper-left", "upper-right"}
MEREO_SYMBOLS = {
    "%p": "part_meronym", "%m": "member_meronym", "%s": "substance_meronym",
    "#p": "part_holonym", "#m": "member_holonym", "#s": "substance_holonym",
}
OUTPUT_NAMES = [
    "tf_spatial_source_bank.json", "tf_spatial_dataset.json",
    "tf_quantitative_source_bank.json", "tf_quantitative_dataset.json",
    "tf_mereological_source_bank.json", "tf_mereological_dataset.json",
    "ext_b_frozen_panel.json", "ext_b_panel_manifest.json",
    "ext_b_construction_provenance.json", "ext_b_freeze_binding.json",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


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


def write_json(path: Path, value: Any) -> None:
    path.write_text(canonical_json(value) + "\n", encoding="utf-8", newline="\n")


def family_id(task_slug: str, source_tuple: Any) -> str:
    payload = "PA-EXT-B-V1-FAMILY\0" + canonical_json(source_tuple)
    return "extb_sf_v2_" + task_slug + "_" + sha256_bytes(payload.encode("utf-8"))


def record_id(family: str, condition: str, role: str) -> str:
    payload = f"PA-EXT-B-V1-RECORD\0{family}\0{condition}\0{role}"
    return "extb_rec_v2_" + sha256_bytes(payload.encode("utf-8"))


def selection_hash(source_tuple: Any) -> str:
    payload = "PA-EXT-B-V1-ORDER\0" + canonical_json(source_tuple)
    return sha256_bytes(payload.encode("utf-8"))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def relation_maps(render: dict[str, Any], task_class: str, relation_key: str | None) -> dict[str, str]:
    fields = render["task_lexical_fields"][task_class]
    result: dict[str, str] = {}
    for key in ("REL_LEX", "REL_LEX_ALT", "OVERT_REL", "IMPLICIT_REL"):
        value = fields[key]
        result[key] = value if isinstance(value, str) else value[relation_key or "left"]
    return result


def render_text(render: dict[str, Any], task_class: str, relation_key: str | None,
                arg_a: str, arg_b: str, condition_id: str, role: str) -> str:
    condition = next(item for item in render["conditions"] if item["condition_id"] == condition_id)
    maps = relation_maps(render, task_class, relation_key)
    if condition_id == "c03_controlled_compression":
        bare = render["c03_relation_lexicalization"][task_class]
        relation = bare if isinstance(bare, str) else bare[relation_key or "left"]
        maps["REL_LEX"] = relation
    values = {
        "ARG_A": arg_a,
        "ARG_B": arg_b,
        "REL_LEX": maps["REL_LEX"],
        "REL_LEX_ALT": maps["REL_LEX_ALT"],
        "OVERT_REL": maps["OVERT_REL"],
        "IMPLICIT_REL": maps["IMPLICIT_REL"],
        "CONTEXT_PHRASE": render["bound_constants"]["CONTEXT_PHRASE"],
        "CONTEXT_PREFIX": render["bound_constants"]["CONTEXT_PREFIX"],
    }
    template = condition["reference_template"] if role == "reference" else condition["realization_template"]
    return surface_string(template.format(**values))


def _spatial_sources() -> list[dict[str, Any]]:
    candidates: list[tuple[str, list[Any], dict[str, Any]]] = []
    seen: set[str] = set()
    with STEPGAME.open("r", encoding="utf-8") as handle:
        for ordinal, line in enumerate(handle):
            row = json.loads(line)
            label = row.get("label") if isinstance(row, dict) else None
            if label not in SPATIAL_LABELS:
                continue
            source_tuple = ["exta_tf_spatial", "6d859381dfd518cae3f073b268aaa323bf4dcf04", ordinal, canonical_string(label)]
            identity = canonical_json(source_tuple)
            if identity in seen:
                continue
            seen.add(identity)
            candidates.append((selection_hash(source_tuple), source_tuple, {"row_ordinal": ordinal, "label": canonical_string(label)}))
    candidates.sort(key=lambda item: (item[0], canonical_json(item[1])))
    selected = candidates[:220]
    if len(selected) != 220:
        raise RuntimeError(f"SPATIAL_SOURCE_INSUFFICIENT_{len(selected)}")
    result = []
    for rank, (order_hash, source_tuple, extra) in enumerate(selected):
        ordinal = extra["row_ordinal"]
        label = extra["label"]
        arg_a = f"extb_spatial_arg_a_{ordinal:06d}"
        arg_b = f"extb_spatial_arg_b_{ordinal:06d}"
        result.append({
            "source_tuple": source_tuple, "selection_hash": order_hash, "selection_rank": rank,
            "source_identity": {"task_id": "exta_tf_spatial", "source_revision": source_tuple[1], "source_row_ordinal": ordinal, "label": label},
            "arg_a": arg_a, "arg_b": arg_b, "relation_key": label,
            "source_provenance": {"source_type": "StepGame", "source_revision": source_tuple[1], "source_sha256": EXPECTED_STEPGAME_SHA, "source_row_ordinal": ordinal, "label": label, "benchmark_fields_excluded": True},
        })
    return result


def _quantitative_sources() -> list[dict[str, Any]]:
    candidates = []
    for index in range(1, 221):
        a = 11 + ((index - 1) % 22)
        b = 4 - ((index - 1) // 22)
        source_tuple = ["exta_tf_quantitative", index, a, b, "ARG_A > ARG_B"]
        candidates.append((selection_hash(source_tuple), source_tuple, index, a, b))
    candidates.sort(key=lambda item: (item[0], canonical_json(item[1])))
    result = []
    for rank, (order_hash, source_tuple, index, a, b) in enumerate(candidates):
        result.append({
            "source_tuple": source_tuple, "selection_hash": order_hash, "selection_rank": rank,
            "source_identity": {"task_id": "exta_tf_quantitative", "global_source_index": index, "numeric_a": a, "numeric_b": b, "comparison_relation": "ARG_A > ARG_B"},
            "arg_a": str(a), "arg_b": str(b), "relation_key": None,
            "source_provenance": {"source_type": "deterministic_program", "formula": "A=11+((i-1) mod 22); B=4-floor((i-1)/22)", "global_source_index": index, "minimum_difference": 7},
        })
    return result


def _parse_wordnet_line(line: str) -> tuple[int, list[str], list[tuple[str, int]]] | None:
    if not line or line.startswith(" ") or line.startswith("#"):
        return None
    left = line.split("|", 1)[0].split()
    if len(left) < 6:
        return None
    try:
        offset = int(left[0])
        word_count = int(left[3], 16)
    except ValueError:
        return None
    cursor = 4
    words: list[str] = []
    for _ in range(word_count):
        if cursor + 1 >= len(left):
            return None
        words.append(left[cursor])
        cursor += 2
    if cursor >= len(left):
        return None
    try:
        pointer_count = int(left[cursor])
    except ValueError:
        return None
    cursor += 1
    pointers: list[tuple[str, int]] = []
    for _ in range(pointer_count):
        if cursor + 3 >= len(left):
            break
        symbol = left[cursor]
        try:
            target = int(left[cursor + 1])
        except ValueError:
            cursor += 4
            continue
        pointers.append((symbol, target))
        cursor += 4
    return offset, words, pointers


def _mereological_sources() -> list[dict[str, Any]]:
    synsets: dict[int, tuple[list[str], list[tuple[str, int]]]] = {}
    with tarfile.open(WORDNET, "r:gz") as archive:
        member = archive.getmember("WordNet-3.0/dict/data.noun")
        stream = archive.extractfile(member)
        if stream is None:
            raise RuntimeError("WORDNET_DATA_NOUN_MISSING")
        for raw in stream:
            parsed = _parse_wordnet_line(raw.decode("utf-8", errors="strict").rstrip("\n"))
            if parsed:
                offset, words, pointers = parsed
                synsets[offset] = (words, pointers)
    candidates: dict[tuple[Any, ...], dict[str, Any]] = {}
    for source_offset in sorted(synsets):
        source_words, pointers = synsets[source_offset]
        for symbol, target_offset in pointers:
            relation = MEREO_SYMBOLS.get(symbol)
            if relation is None or target_offset not in synsets:
                continue
            target_words = synsets[target_offset][0]
            if symbol.startswith("#"):
                part_words, whole_words = source_words, target_words
            else:
                part_words, whole_words = target_words, source_words
            parts = sorted({canonical_string(word) for word in part_words if canonical_string(word)})
            wholes = sorted({canonical_string(word) for word in whole_words if canonical_string(word)})
            if not parts or not wholes:
                continue
            part, whole = parts[0], wholes[0]
            source_tuple = ["exta_tf_mereological", relation, part, whole, str(source_offset), str(target_offset)]
            candidates[tuple(source_tuple)] = {"source_tuple": source_tuple, "source_offset": source_offset, "target_offset": target_offset, "relation": relation, "part": part, "whole": whole, "pointer_type": symbol}
    ordered = []
    for item in candidates.values():
        ordered.append((selection_hash(item["source_tuple"]), item["source_tuple"], item))
    ordered.sort(key=lambda item: (item[0], canonical_json(item[1])))
    selected = ordered[:220]
    if len(selected) != 220:
        raise RuntimeError(f"MEREOLOGICAL_SOURCE_INSUFFICIENT_{len(selected)}")
    result = []
    for rank, (order_hash, source_tuple, item) in enumerate(selected):
        result.append({
            "source_tuple": source_tuple, "selection_hash": order_hash, "selection_rank": rank,
            "source_identity": {"task_id": "exta_tf_mereological", "normalized_relation_type": item["relation"], "part_lemma": item["part"], "whole_lemma": item["whole"], "source_synset_offset": item["source_offset"], "target_synset_offset": item["target_offset"], "pointer_type": item["pointer_type"]},
            "arg_a": item["part"], "arg_b": item["whole"], "relation_key": None,
            "source_provenance": {"source_type": "WordNet-3.0", "source_sha256": EXPECTED_WORDNET_SHA, "source_synset_offset": item["source_offset"], "target_synset_offset": item["target_offset"], "pointer_type": item["pointer_type"], "glosses_excluded": True},
        })
    return result


def _split_for_rank(rank: int) -> tuple[str, int, str]:
    condition = CONDITIONS[rank // 22]
    within = rank % 22 + 1
    split = "FIT" if within <= 6 else "DIAGNOSTIC" if within <= 14 else "EVAL"
    return condition, within, split


def _task_objects(task_class: str, task_id: str, slug: str, sources: list[dict[str, Any]], render: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    bank = []
    records = []
    for source in sources:
        family = family_id(slug, source["source_tuple"])
        bank.append({
            "schema_version": "1.0.0", "study_id": "PA-EXT-B", "task_id": task_id, "task_slug": slug,
            "source_family_id": family, "source_identity": source["source_identity"], "canonical_source_tuple": source["source_tuple"],
            "arg_a": source["arg_a"], "arg_b": source["arg_b"], "semantic_relation": "exta_rel_spatial_configuration" if slug == "spatial" else "exta_rel_quantitative_comparison" if slug == "quantitative" else "exta_rel_part_whole",
            "relation_orientation": "ARG_A relative to ARG_B" if slug == "spatial" else "ARG_A > ARG_B" if slug == "quantitative" else "ARG_A is part/member/substance of ARG_B",
            "selection_hash": source["selection_hash"], "selection_rank": source["selection_rank"], "source_provenance": source["source_provenance"],
        })
        assigned_condition, _within, assigned_split = _split_for_rank(source["selection_rank"])
        arg_a = source["arg_a"].replace("_", " ") if slug == "mereological" else source["arg_a"]
        arg_b = source["arg_b"].replace("_", " ") if slug == "mereological" else source["arg_b"]
        text_a = render_text(render, task_class, source["relation_key"], surface_string(arg_a), surface_string(arg_b), assigned_condition, "reference")
        text_b = render_text(render, task_class, source["relation_key"], surface_string(arg_a), surface_string(arg_b), assigned_condition, "realization")
        for role, text in (("reference", text_a), ("realization", text_b)):
            records.append({
                "schema_version": "1.0.0", "study_id": "PA-EXT-B", "task_id": task_id, "task_slug": slug, "label": task_class,
                "family_id": family, "record_id": record_id(family, assigned_condition, role), "record_role": role, "split": assigned_split,
                "condition_id": assigned_condition, "arg_a": surface_string(arg_a), "arg_b": surface_string(arg_b),
                "semantic_relation": bank[-1]["semantic_relation"], "rendered_text": text, "source_identity": source["source_identity"],
                "selection_rank": source["selection_rank"], "source_provenance": source["source_provenance"],
            })
    records.sort(key=lambda row: (row["split"], CONDITIONS.index(row["condition_id"]), row["family_id"], row["record_role"]))
    return {"schema_version": "1.0.0", "study_id": "PA-EXT-B", "task_id": task_id, "task_slug": slug, "label": task_class, "family_count": len(bank), "record_count": len(records), "source_families": bank, "records": records}, records


def _content_hash(path: Path) -> str:
    return sha256(path)


def build() -> None:
    if DATA.exists() or (BASE / "paper_a_ext_b_frozen_panel.json").exists() or (BASE / "paper_a_ext_b_panel_manifest.json").exists():
        raise RuntimeError("PRODUCTION_OUTPUT_ALREADY_EXISTS")
    if sha256(STEPGAME) != EXPECTED_STEPGAME_SHA or sha256(WORDNET) != EXPECTED_WORDNET_SHA:
        raise RuntimeError("SOURCE_IDENTITY_MISMATCH")
    render = load_json(V2_RENDER)
    sources_by_task = {"spatial": _spatial_sources(), "quantitative": _quantitative_sources(), "mereological": _mereological_sources()}
    task_objects: dict[str, dict[str, Any]] = {}
    task_records: dict[str, list[dict[str, Any]]] = {}
    for task_class, task_id, slug in TASKS:
        task_objects[slug], task_records[slug] = _task_objects(task_class, task_id, slug, sources_by_task[slug], render)
    combined = [row for slug in ("spatial", "quantitative", "mereological") for row in task_records[slug]]
    if len(combined) != 1320 or len({row["family_id"] for row in combined}) != 660:
        raise RuntimeError("COUNT_GATE_FAILED")
    exact = [row["rendered_text"] for row in combined]
    normalized = [canonical_string(text) for text in exact]
    if len(set(exact)) != len(exact) or len(set(normalized)) != len(normalized):
        raise RuntimeError("DUPLICATE_GATE_FAILED")
    temporary = Path(tempfile.mkdtemp(prefix="paper_a_ext_b_v2_"))
    try:
        temp_data = temporary / "data"
        temp_data.mkdir()
        task_files = {"spatial": "tf_spatial_dataset.json", "quantitative": "tf_quantitative_dataset.json", "mereological": "tf_mereological_dataset.json"}
        bank_files = {"spatial": "tf_spatial_source_bank.json", "quantitative": "tf_quantitative_source_bank.json", "mereological": "tf_mereological_source_bank.json"}
        for slug in task_files:
            write_json(temp_data / task_files[slug], task_objects[slug])
            write_json(temp_data / bank_files[slug], task_objects[slug]["source_families"])
        panel = {"schema_version": "1.0.0", "study_id": "PA-EXT-B", "panel_id": "PA-EXT-B-V2-FROZEN-PANEL", "family_count": 660, "record_count": 1320, "records": combined, "model_inference_performed": False, "scientific_result_created": False}
        write_json(temp_data / "ext_b_frozen_panel.json", panel)
        artifact_rel = {
            **{f"experiments/paper_a_ext_b/data/{name}": _content_hash(temp_data / name) for name in (*bank_files.values(), *task_files.values())},
            "experiments/paper_a_ext_b/data/ext_b_frozen_panel.json": _content_hash(temp_data / "ext_b_frozen_panel.json"),
        }
        schema_paths = [V2_SOURCE_SCHEMA, V2_RECORD_SCHEMA, V2_PANEL_SCHEMA, V2_PROVENANCE_SCHEMA]
        manifest = {
            "schema_version": "1.0.0", "study_id": "PA-EXT-B", "manifest_id": "PA-EXT-B-V2-PANEL-MANIFEST",
            "authority_hashes": {"amendment_v2": sha256(V2_AMENDMENT), "spec_v2": sha256(V2_SPEC), "rendering_v2": sha256(V2_RENDER)},
            "amendment_v1_sha256": sha256(BASE / "paper_a_ext_b_construction_amendment_v1.json"), "amendment_v2_sha256": sha256(V2_AMENDMENT),
            "source_bank_hashes": {slug: artifact_rel[f"experiments/paper_a_ext_b/data/{bank_files[slug]}"] for slug in bank_files},
            "task_dataset_hashes": {slug: artifact_rel[f"experiments/paper_a_ext_b/data/{task_files[slug]}"] for slug in task_files},
            "combined_panel_sha256": artifact_rel["experiments/paper_a_ext_b/data/ext_b_frozen_panel.json"],
            "validator_hashes": {"static": sha256(BASE / "validate_paper_a_ext_b_construction_v2.py"), "production": sha256(ROOT / VALIDATOR_REL)},
            "family_counts": {slug: 220 for slug in task_files} | {"total": 660},
            "record_counts": {slug: 440 for slug in task_files} | {"total": 1320},
            "class_counts": {"TF_SPATIAL": 440, "TF_QUANTITATIVE": 440, "TF_MEREOLOGICAL": 440},
            "split_counts": {"FIT": 360, "DIAGNOSTIC": 480, "EVAL": 480},
            "condition_counts": {condition: 132 for condition in CONDITIONS},
            "schema_hashes": {path.name: sha256(path) for path in schema_paths},
            "generated_at_utc_metadata_only": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "model_inference_performed": False, "scientific_result_created": False,
        }
        write_json(temp_data / "ext_b_panel_manifest.json", manifest)
        provenance = {
            "input_source_identities": {"stepgame_train": {"path": str(STEPGAME), "revision": "6d859381dfd518cae3f073b268aaa323bf4dcf04", "sha256": EXPECTED_STEPGAME_SHA}, "wordnet_3_0": {"path": str(WORDNET), "version": "3.0", "sha256": EXPECTED_WORDNET_SHA}},
            "generation_identity": {"builder_path": BUILDER_REL, "builder_sha256": sha256(ROOT / BUILDER_REL), "canonical_json_rule": "UTF-8, ensure_ascii=false, sorted keys, compact separators, one LF", "scientific_payload_timestamp_excluded": True},
            "construction_specification_identity": {"spec_path": "experiments/paper_a_ext_b/paper_a_ext_b_construction_spec_v2.json", "sha256": sha256(V2_SPEC)},
            "rendering_identity": {"path": "experiments/paper_a_ext_b/paper_a_ext_b_rendering_conditions_c01_c10_v2.json", "sha256": sha256(V2_RENDER)},
            "validation_identity": {"static_validator": sha256(BASE / "validate_paper_a_ext_b_construction_v2.py"), "production_validator": sha256(ROOT / VALIDATOR_REL)},
            "generation_timestamp_metadata_only": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "canonical_hashes": artifact_rel,
            "three_of_three_gate_state": {"SPATIAL_READY": True, "QUANTITATIVE_READY": True, "MEREOLOGICAL_READY": True, "EXT_B_3_OF_3_DATASET_GATE_PASS": True},
            "model_inference_performed": False, "scientific_result_created": False,
        }
        write_json(temp_data / "ext_b_construction_provenance.json", provenance)
        binding = {"binding_id": "PA-EXT-B-V2-FREEZE-BINDING", "status": "FROZEN_SOURCE_ONLY_PRE_MODEL_OUTCOME", "authority_hashes": {"amendment_v2": sha256(V2_AMENDMENT), "spec_v2": sha256(V2_SPEC), "rendering_v2": sha256(V2_RENDER), "static_validator": sha256(BASE / "validate_paper_a_ext_b_construction_v2.py")}, "source_hashes": {"stepgame": EXPECTED_STEPGAME_SHA, "wordnet": EXPECTED_WORDNET_SHA}, "production_artifact_hashes": artifact_rel, "provenance_sha256": _content_hash(temp_data / "ext_b_construction_provenance.json"), "model_inference_performed": False, "scientific_result_created": False, "self_hash_policy": "The binding excludes its own hash; Git binds the committed bytes."}
        write_json(temp_data / "ext_b_freeze_binding.json", binding)
        DATA.mkdir(parents=True)
        for name in OUTPUT_NAMES:
            shutil.copy2(temp_data / name, DATA / name)
    finally:
        shutil.rmtree(temporary, ignore_errors=True)
    print("EXT_B_V2_PRODUCTION_BUILD=PASS")
    print("SPATIAL_FAMILIES=220")
    print("QUANTITATIVE_FAMILIES=220")
    print("MEREOLOGICAL_FAMILIES=220")
    print("COMBINED_FAMILIES=660")
    print("COMBINED_RECORDS=1320")
    print("MODEL_INFERENCE_RUN=false")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true", required=True)
    args = parser.parse_args()
    build()
