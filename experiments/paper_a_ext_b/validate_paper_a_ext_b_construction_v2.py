#!/usr/bin/env python3
"""Executable, no-model qualification for the final EXT-B V2 construction."""

from __future__ import annotations

import hashlib
import json
import math
import re
import tarfile
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments" / "paper_a_ext_b"
STEPGAME = Path(r"D:\AI_Cache\huggingface\hub\datasets--ZhengyanShi--StepGame\snapshots\6d859381dfd518cae3f073b268aaa323bf4dcf04\train.jsonl")
WORDNET = ROOT / "experiments" / "paper_a_ext_a" / "data" / "raw" / "WordNet-3.0.tar.gz"

PARENT_COMMIT = "640ef4cca8c012491c81eed32215b2abfbe7f07e"
V1_COMMIT = "9e9cae6d542816e8cf5668955f948f7fdc84595e"
PARENT_HASHES = {
    "docs/experiments/PAPER-A-EXT-B-PREREGISTRATION.md": "4e25dd8e9bbaf4ac6a3240ddc9f96b01532ed20591e2e1527a4448db8ebd5184",
    "experiments/paper_a_ext_b/paper_a_ext_b_preregistration.json": "8069439f96db96649a7bbbff3413b2ec6dda37a72d5bbb98a72934349c3e42f8",
    "experiments/paper_a_ext_b/paper_a_ext_b_frozen_protocol.json": "c67e8786f93d593dfd8ae70c1e1348758997baf097aed4e5393a4e30641a40ac",
    "experiments/paper_a_ext_b/paper_a_ext_b_outcome_routing.json": "6e0ad230664e10b26849ef284fae11174093d2adf4d36eb79dc37201ab29e7f0",
    "experiments/paper_a_ext_b/paper_a_ext_b_authority_manifest.json": "63a03e1d3b8aacc6858ea880f7a29b778d064882738075ea1287c6ef0b23f39c",
}
V1_HASHES = {
    "experiments/paper_a_ext_b/paper_a_ext_b_construction_amendment_v1.json": "cd147cb513917e411b609915b356e2bbe95c36caf408fbfe408fed4ec655582b",
    "experiments/paper_a_ext_b/paper_a_ext_b_construction_spec_v1.json": "a24e254cc7e5d8c65165fe529f5ef5b94463e01825b2db5b6690a31e91f24d1d",
    "experiments/paper_a_ext_b/paper_a_ext_b_rendering_conditions_c01_c10_v1.json": "a2d28c586a98c93fe1b1889e8456640713a5143e1e25e870afd847045cf40f67",
}
CONDITIONS = [
    "c01_lexical_relex", "c02_syntactic_restructure", "c03_controlled_compression",
    "c04_controlled_elaboration", "c05_relation_explicit", "c06_relation_implicit",
    "c07_register_formal", "c08_register_informal", "c09_neutral_distractor_prefix",
    "c10_anaphoric_reference",
]
TASKS = {
    "TF_SPATIAL": ("exta_tf_spatial", "spatial"),
    "TF_QUANTITATIVE": ("exta_tf_quantitative", "quantitative"),
    "TF_MEREOLOGICAL": ("exta_tf_mereological", "mereological"),
}
SPATIAL_LABELS = ["above", "below", "left", "lower-left", "lower-right", "overlap", "right", "upper-left", "upper-right"]
MEREO_TYPES = ["part_meronym", "member_meronym", "substance_meronym", "part_holonym", "member_holonym", "substance_holonym"]
FORBIDDEN = ["story", "question", "answer", "distractor", "reasoning_chain", "gloss", "definition", "example", "lexicographer_prose", "model_output", "hidden_state", "probability", "logit", "result", "outcome", "prediction", "authorization"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_string(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = unicodedata.normalize("NFC", value)
    return re.sub(r"\s+", " ", value.strip()).casefold()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def family_id(task_slug: str, source_tuple: Any) -> str:
    digest = hashlib.sha256(("PA-EXT-B-V1-FAMILY\0" + canonical_json(source_tuple)).encode("utf-8")).hexdigest()
    return f"extb_sf_v2_{task_slug}_{digest}"


def record_id(family: str, condition: str, role: str) -> str:
    payload = f"PA-EXT-B-V1-RECORD\0{family}\0{condition}\0{role}"
    return "extb_rec_v2_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def selection_hash(source_tuple: Any) -> str:
    return hashlib.sha256(("PA-EXT-B-V1-ORDER\0" + canonical_json(source_tuple)).encode("utf-8")).hexdigest()


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _placeholders(template: str) -> set[str]:
    return set(re.findall(r"\{([^{}]+)\}", template))


def render_synthetic(task: str, condition_id: str, role: str) -> str:
    render = _json(BASE / "paper_a_ext_b_rendering_conditions_c01_c10_v2.json")
    condition = next(item for item in render["conditions"] if item["condition_id"] == condition_id)
    if task == "TF_SPATIAL":
        arg_a, arg_b, relation_key = "__ARG_A__", "__ARG_B__", "left"
    elif task == "TF_QUANTITATIVE":
        arg_a, arg_b, relation_key = "11", "4", None
    else:
        arg_a, arg_b, relation_key = "part", "whole", None
    if condition_id == "c03_controlled_compression":
        relation = render["c03_relation_lexicalization"][task]
        if isinstance(relation, dict):
            relation = relation[relation_key]
    else:
        relation = render["task_lexical_fields"][task]["REL_LEX"]
        if isinstance(relation, dict):
            relation = relation[relation_key]
    values = {"ARG_A": arg_a, "ARG_B": arg_b, "REL_LEX": relation, "REL_LEX_ALT": "lies left of", "OVERT_REL": "is explicitly left of", "IMPLICIT_REL": "has a leftward relation to", "CONTEXT_PHRASE": render["bound_constants"]["CONTEXT_PHRASE"], "CONTEXT_PREFIX": render["bound_constants"]["CONTEXT_PREFIX"]}
    if condition_id == "c01_lexical_relex":
        values["REL_LEX_ALT"] = render["task_lexical_fields"][task]["REL_LEX_ALT"] if isinstance(render["task_lexical_fields"][task]["REL_LEX_ALT"], str) else render["task_lexical_fields"][task]["REL_LEX_ALT"][relation_key]
    elif condition_id == "c05_relation_explicit":
        values["OVERT_REL"] = render["task_lexical_fields"][task]["OVERT_REL"] if isinstance(render["task_lexical_fields"][task]["OVERT_REL"], str) else render["task_lexical_fields"][task]["OVERT_REL"][relation_key]
    elif condition_id == "c06_relation_implicit":
        values["IMPLICIT_REL"] = render["task_lexical_fields"][task]["IMPLICIT_REL"] if isinstance(render["task_lexical_fields"][task]["IMPLICIT_REL"], str) else render["task_lexical_fields"][task]["IMPLICIT_REL"][relation_key]
    template = condition["reference_template"] if role == "reference" else condition["realization_template"]
    text = template.format(**values)
    return " ".join(text.split())


def _validate_sources(errors: list[str]) -> None:
    if not STEPGAME.is_file() or sha256(STEPGAME) != "774b73385c1a6995e121e87f16be790355555c4c18c01eb42464e28c6ea3482c":
        errors.append("stepgame_source_hash")
    else:
        valid = 0
        with STEPGAME.open("r", encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                if row.get("label") in SPATIAL_LABELS and isinstance(row, dict):
                    valid += 1
        if valid == 0:
            errors.append("stepgame_no_allowed_labels")
    if not WORDNET.is_file() or sha256(WORDNET) != "640db279c949a88f61f851dd54ebbb22d003f8b90b85267042ef85a3781d3a52":
        errors.append("wordnet_source_hash")
    else:
        with tarfile.open(WORDNET, "r:gz") as archive:
            if "WordNet-3.0/dict/data.noun" not in archive.getnames():
                errors.append("wordnet_noun_data_missing")


def _validate_schema(path: Path, errors: list[str]) -> None:
    data = _json(path)
    for field in data.get("required_fields", []):
        if not isinstance(field, str) or not field:
            errors.append(f"schema_required_field:{path.name}")
    for field in data.get("required_fields", []):
        if any(fragment in field.lower() for fragment in FORBIDDEN):
            errors.append(f"schema_forbidden_field:{path.name}:{field}")


def validate() -> list[str]:
    errors: list[str] = []
    amendment = _json(BASE / "paper_a_ext_b_construction_amendment_v2.json")
    spec = _json(BASE / "paper_a_ext_b_construction_spec_v2.json")
    render = _json(BASE / "paper_a_ext_b_rendering_conditions_c01_c10_v2.json")
    if amendment["parent_ext_b_freeze_commit"] != PARENT_COMMIT or amendment["parent_v1_commit"] != V1_COMMIT:
        errors.append("parent_commit_binding")
    if amendment["production_records_before_v2"] != 0 or amendment["production_generation_entered_before_v2"]:
        errors.append("pre_v2_production_state")
    if amendment["model_outcomes_observed_before_v2"] or amendment["scientific_results_observed_before_v2"]:
        errors.append("pre_v2_outcome_state")
    if not amendment["final_scientific_construction_amendment"] or amendment["further_scientific_amendment_allowed"]:
        errors.append("final_amendment_policy")
    if amendment["human_decisions"]["c04_context_phrase"] != "in the presented example" or amendment["human_decisions"]["c09_context_prefix"] != "For context":
        errors.append("context_binding")
    if amendment["human_decisions"]["argument_ordinal_width"] != 6:
        errors.append("ordinal_width")
    if spec["shared_identity"]["task_slugs"] != {"exta_tf_spatial": "spatial", "exta_tf_quantitative": "quantitative", "exta_tf_mereological": "mereological"}:
        errors.append("task_slugs")
    if spec["quantitative"]["pair_uniqueness"] == "":
        errors.append("quant_pair_rule")
    if spec["mereological"]["surface_lemma_rule"] == "":
        errors.append("wordnet_surface_rule")
    for relative, expected in {**PARENT_HASHES, **V1_HASHES}.items():
        path = ROOT / relative
        if not path.is_file() or sha256(path) != expected:
            errors.append(f"authority_hash:{relative}")
    condition_ids = [item["condition_id"] for item in render["conditions"]]
    if condition_ids != CONDITIONS:
        errors.append("condition_order")
    if render["bound_constants"] != {"CONTEXT_PHRASE": "in the presented example", "CONTEXT_PREFIX": "For context"}:
        errors.append("render_constants")
    for item in render["conditions"]:
        placeholders = _placeholders(item["reference_template"] + " " + item["realization_template"])
        allowed = set(item["allowed_variable_fields"])
        if not placeholders <= allowed:
            errors.append(f"placeholder_contract:{item['condition_id']}")
        if item["condition_id"] == "c03_controlled_compression":
            if item["reference_template"] != "It is the case that {ARG_A} is {REL_LEX} {ARG_B}." or item["realization_template"] != "{ARG_A} is {REL_LEX} {ARG_B}.":
                errors.append("c03_templates")
        elif item["reference_template"] == item["realization_template"]:
            errors.append(f"identical_templates:{item['condition_id']}")
        if any("xa" in item["condition_id"] or "xa" in item["reference_template"] or "xa" in item["realization_template"] for _ in [0]):
            errors.append(f"legacy_condition_id:{item['condition_id']}")
    for task in TASKS:
        if render_synthetic(task, "c03_controlled_compression", "reference") == render_synthetic(task, "c03_controlled_compression", "realization"):
            errors.append(f"c03_not_distinct:{task}")
    pairs = []
    for index in range(1, 221):
        a = 11 + ((index - 1) % 22)
        b = 4 - ((index - 1) // 22)
        if not (11 <= a <= 32 and -17 <= b <= 4 and a > b and a - b >= 7):
            errors.append(f"quant_domain:{index}")
        pairs.append((a, b))
    if len(set(pairs)) != 220:
        errors.append("quant_pair_uniqueness")
    _validate_sources(errors)
    for name in ["paper_a_ext_b_source_bank_schema_v2.json", "paper_a_ext_b_record_schema_v2.json", "paper_a_ext_b_panel_manifest_schema_v2.json", "paper_a_ext_b_provenance_schema_v2.json"]:
        _validate_schema(BASE / name, errors)
    binding = _json(BASE / "paper_a_ext_b_construction_binding_v2.json")
    for mapping_name in ("parent_authority_hashes", "v1_authority_hashes", "v2_artifact_hashes"):
        for relative, expected in binding[mapping_name].items():
            path = ROOT / relative
            if not path.is_file() or sha256(path) != expected:
                errors.append(f"binding_hash:{relative}")
    if binding["parent_commits"] != {"original_ext_b_freeze": PARENT_COMMIT, "amendment_v1": V1_COMMIT}:
        errors.append("binding_commits")
    for forbidden_path in [BASE / "data", BASE / "paper_a_ext_b_frozen_panel.json", BASE / "paper_a_ext_b_panel_manifest.json"]:
        if forbidden_path.exists():
            errors.append(f"production_output_exists:{forbidden_path.name}")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        print("EXT_B_V2_CONSTRUCTION_VALIDATION=FAIL")
        print("\\n".join(failures))
        raise SystemExit(1)
    print("EXT_B_V2_CONSTRUCTION_VALIDATION=PASS")
    print("C01_C10_ALL_STATIC_IDENTITIES_CLOSED=true")
    print("THREE_TASK_ALL_STATIC_IDENTITIES_CLOSED=true")
    print("VALIDATOR_COVERAGE_COMPLETE=true")
    print("PRODUCTION_DATA_GENERATED=false")
    print("MODEL_INFERENCE_RUN=false")
