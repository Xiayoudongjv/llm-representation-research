"""One-shot offline confirmation for TEMPORAL_EVENT_LIKE_V1.

This module evaluates the frozen SOURCE_CONFIRMATION identity manifest against
the immutable V8 cached metadata/classes and the TEMP-FEAS-002E ontology
snapshot.  It intentionally has no network or model-loading path and never
creates a canonical temporal asset bank or panel.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


HERE = Path(__file__).resolve()
EXP_DIR = HERE.parents[2]
ENGINEERING_DIR = EXP_DIR / "engineering"
OUTPUT_DIR = ENGINEERING_DIR / "temp_feas_002r"
RAW_DIR = EXP_DIR / "data" / "raw" / "wikidata_v8"
TEMP001_DIR = ENGINEERING_DIR / "temp_feas_001"
TEMP002E_DIR = ENGINEERING_DIR / "temp_feas_002e"

RULE_PATH = TEMP001_DIR / "temp_feas_001_proposed_rule.json"
CONFIRMATION_MANIFEST_PATH = TEMP001_DIR / "source_confirmation_manifest.json"
POOL_MANIFEST_PATH = TEMP001_DIR / "date_valid_pool_manifest.json"
V8_AUTHORITY_PATH = EXP_DIR / "paper_a_ext_a_temporal_asset_source_v8.json"
V8_CHECKPOINT_PATH = RAW_DIR / "acquisition_checkpoint.json"
ONTOLOGY_CLOSURE_PATH = TEMP002E_DIR / "ontology_closure_status.json"
ONTOLOGY_EDGES_PATH = TEMP002E_DIR / "ontology_direct_edges.json"
ONTOLOGY_REPORT_PATH = TEMP002E_DIR / "temp_feas_002e_report.json"

EXPECTED_HEAD = "36015e5cd9d7f95da2b9b82d7ed3e1b5b930545d"
EXPECTED_PROPOSAL_SHA = "5ac334a8e788b6c491cf9af375c4926c1db8bda6fd71b53e16ff3dd68b22a9be"
EXPECTED_CONFIRMATION_SHA = "3a278b4602aadc361a998eff0910571daae292255beae536c37249efa09843ec"
EXPECTED_POOL_SHA = "860351f16efa05c8991ee3fc76b7324b0d7a3c383a525e7f7f6c3d85e0f4d592"
EXPECTED_ONTOLOGY_AUTHORITY_SHA = "cef7da7d6bbfe55f5c754b56e28aa88e93f261eebe8b44d8c6a12f8b4d64dbc1"
EXPECTED_V8_AUTHORITY_SHA = "47a2ce443fe097b32fc391b910d97860593093ec19c9e362ec7019d5f3984ca7"
EXPECTED_V8_CHECKPOINT_SHA = "a6f21f6bdf2267d14c36f26231a61d8279ed1bbe66ce0265e25c6fde61a59b38"
ROOTS = ("Q1656682", "Q1190554")
GREGORIAN_QID = "Q1985727"
MIN_PRECISION = 11
PAGE_SIZE = 100
METADATA_BATCH_SIZE = 50
DATE_RE = re.compile(r"\|(?P<date>[^|]+)\|(?P<time>[^|]+)\|precision=(?P<precision>\d+)\|calendar=(?P<calendar>Q\d+)$")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def content_hash(value: dict[str, Any]) -> str:
    without_hash = {key: val for key, val in value.items() if key != "artifact_sha256"}
    return sha256_bytes(canonical_json(without_hash))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_hashed_json(path: Path, value: dict[str, Any]) -> str:
    result = dict(value)
    result["artifact_sha256"] = content_hash(result)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result["artifact_sha256"]


def file_sha(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git_value(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=EXP_DIR.parent.parent, text=True).strip()


def verify_entry_gate() -> dict[str, Any]:
    head = git_value("rev-parse", "HEAD")
    origin = git_value("rev-parse", "origin/main")
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=EXP_DIR.parent.parent).returncode == 0
    rule = read_json(RULE_PATH)
    confirmation = read_json(CONFIRMATION_MANIFEST_PATH)
    pool = read_json(POOL_MANIFEST_PATH)
    closure = read_json(ONTOLOGY_CLOSURE_PATH)
    ontology_report = read_json(ONTOLOGY_REPORT_PATH)
    v8_authority = read_json(V8_AUTHORITY_PATH)
    checkpoint_sha = file_sha(V8_CHECKPOINT_PATH)
    ontology_authority = ontology_report.get("snapshot_authority_sha256")
    gate = {
        "head": head,
        "origin_main": origin,
        "staging_empty": staged,
        "proposal_sha_valid": rule.get("proposal_sha256") == EXPECTED_PROPOSAL_SHA,
        "confirmation_manifest_sha_valid": confirmation.get("manifest_sha256") == EXPECTED_CONFIRMATION_SHA,
        "source_pool_sha_valid": pool.get("manifest_sha256") == EXPECTED_POOL_SHA,
        "ontology_snapshot_sha_valid": ontology_authority == EXPECTED_ONTOLOGY_AUTHORITY_SHA,
        "ontology_unresolved_seed_count": closure.get("unresolved_seed_count"),
        "v8_authority_unchanged": file_sha(V8_AUTHORITY_PATH) == EXPECTED_V8_AUTHORITY_SHA,
        "v8_checkpoint_unchanged": checkpoint_sha == EXPECTED_V8_CHECKPOINT_SHA,
        "v8_lineage_formal_result_absent": not (EXP_DIR / "data" / "wikidata_temporal_source_families_v8.json").exists(),
        "formal_inference_performed": False,
        "confirmation_semantics_accessed_before_gate": False,
        "network_accessed": False,
    }
    gate["pass"] = all(
        [
            head == EXPECTED_HEAD,
            origin == EXPECTED_HEAD,
            staged,
            gate["proposal_sha_valid"],
            gate["confirmation_manifest_sha_valid"],
            gate["source_pool_sha_valid"],
            gate["ontology_snapshot_sha_valid"],
            gate["ontology_unresolved_seed_count"] == 0,
            gate["v8_authority_unchanged"],
            gate["v8_checkpoint_unchanged"],
            gate["v8_lineage_formal_result_absent"],
        ]
    )
    if not gate["pass"]:
        raise RuntimeError("TEMP_FEAS_002R_ENTRY_GATE_FAILED:" + json.dumps(gate, sort_keys=True))
    return gate


def _v8_module() -> Any:
    import sys

    sys.path.insert(0, str(EXP_DIR))
    return importlib.import_module("acquire_wikidata_temporal_v8")


def load_frozen_candidates(v8: Any) -> list[dict[str, str]]:
    """Load only the 0--6500 cached candidate pages used by TEMP-FEAS-001."""
    payloads: list[dict[str, Any]] = []
    for offset in range(0, 6600, PAGE_SIZE):
        query = v8.candidate_query(limit=PAGE_SIZE, offset=offset)
        path = RAW_DIR / f"candidate_page_offset_{offset:08d}_{v8.query_sha256(query)[:16]}.json"
        meta = path.with_suffix(".meta.json")
        if not path.exists() or not meta.exists():
            raise RuntimeError(f"MISSING_FROZEN_CANDIDATE_PAGE_{offset}")
        raw = path.read_bytes()
        metadata = read_json(meta)
        if metadata.get("query_sha256") != v8.query_sha256(query) or metadata.get("payload_sha256") != sha256_bytes(raw):
            raise RuntimeError(f"CANDIDATE_PAGE_IDENTITY_MISMATCH_{offset}")
        payloads.append(json.loads(raw.decode("utf-8")))
    return v8._parse_candidates(payloads)


def parse_confirmation_identity(value: str) -> dict[str, Any]:
    qid, remainder = value.split("|", 1)
    match = DATE_RE.search("|" + remainder)
    if not match:
        raise ValueError(f"INVALID_CANONICAL_IDENTITY:{value}")
    return {
        "canonical_identity": value,
        "wikidata_item_id": qid,
        "accepted_date": match.group("date"),
        "p585_point_in_time_value": match.group("time"),
        "date_precision": int(match.group("precision")),
        "calendar_model": match.group("calendar"),
    }


def bindings(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return list(payload.get("results", {}).get("bindings", []))


def value(binding: dict[str, Any], key: str) -> str | None:
    item = binding.get(key, {})
    result = item.get("value")
    return result if isinstance(result, str) else None


def qid_from_uri(uri: str | None) -> str | None:
    if not uri:
        return None
    qid = uri.rsplit("/", 1)[-1]
    return qid if re.fullmatch(r"Q[1-9][0-9]*", qid) else None


def parse_metadata(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, set[Any]]] = defaultdict(lambda: {"labels": set(), "records": set()})
    for row in bindings(payload):
        qid = qid_from_uri(value(row, "item"))
        label = value(row, "label")
        date = value(row, "date")
        time_value = value(row, "timeValue")
        precision = value(row, "precision")
        calendar = qid_from_uri(value(row, "calendar"))
        if qid and label and date and time_value and precision and calendar:
            grouped[qid]["labels"].add(label)
            grouped[qid]["records"].add((date, time_value, int(precision), calendar))
    return grouped


def parse_classes(payload: dict[str, Any]) -> dict[str, set[str]]:
    grouped: dict[str, set[str]] = defaultdict(set)
    for row in bindings(payload):
        qid = qid_from_uri(value(row, "item"))
        clazz = qid_from_uri(value(row, "class"))
        if qid and clazz:
            grouped[qid].add(clazz)
    return grouped


def load_cached_semantics(v8: Any, candidates: list[dict[str, str]], qids: set[str]) -> tuple[dict[str, dict[str, Any]], dict[str, set[str]]]:
    positions = {row["wikidata_item_id"]: index for index, row in enumerate(candidates)}
    wanted_batches = sorted({(positions[qid] // METADATA_BATCH_SIZE) * METADATA_BATCH_SIZE for qid in qids})
    metadata: dict[str, dict[str, Any]] = {}
    classes: dict[str, set[str]] = defaultdict(set)
    for start in wanted_batches:
        batch_qids = [row["wikidata_item_id"] for row in candidates[start : start + METADATA_BATCH_SIZE]]
        identity = f"batch_{start:08d}"
        for kind, query in (("metadata", v8._metadata_query(batch_qids)), ("class", v8._class_query(batch_qids))):
            path = RAW_DIR / f"{kind}_chunk_{identity}_{v8.query_sha256(query)[:16]}.json"
            meta_path = path.with_suffix(".meta.json")
            if not path.exists() or not meta_path.exists():
                raise RuntimeError(f"MISSING_CACHED_{kind.upper()}_CHUNK_{start}")
            raw = path.read_bytes()
            meta = read_json(meta_path)
            if meta.get("query_sha256") != v8.query_sha256(query) or meta.get("payload_sha256") != sha256_bytes(raw):
                raise RuntimeError(f"CACHED_{kind.upper()}_IDENTITY_MISMATCH_{start}")
            parsed = json.loads(raw.decode("utf-8"))
            if kind == "metadata":
                for qid, record in parse_metadata(parsed).items():
                    if qid in qids:
                        metadata[qid] = record
            else:
                for qid, values in parse_classes(parsed).items():
                    if qid in qids:
                        classes[qid].update(values)
    return metadata, classes


def load_ontology() -> tuple[dict[str, set[str]], dict[str, str]]:
    edges_payload = read_json(ONTOLOGY_EDGES_PATH)
    adjacency: dict[str, set[str]] = defaultdict(set)
    for edge in edges_payload["edges"]:
        adjacency[edge["source_qid"]].update(edge["direct_p279_qids"])
    statuses = read_json(ONTOLOGY_CLOSURE_PATH)["seed_statuses"]
    return adjacency, statuses


def root_reachability(start: str, adjacency: dict[str, set[str]], memo: dict[str, frozenset[str]], active: set[str] | None = None) -> frozenset[str]:
    if start in memo:
        return memo[start]
    if active is None:
        active = set()
    if start in active:
        return frozenset()
    if start in ROOTS:
        result = frozenset({start})
        memo[start] = result
        return result
    active.add(start)
    found: set[str] = set()
    for parent in adjacency.get(start, set()):
        found.update(root_reachability(parent, adjacency, memo, active))
    active.remove(start)
    result = frozenset(found)
    memo[start] = result
    return result


def root_status(classes: Iterable[str], adjacency: dict[str, set[str]], memo: dict[str, frozenset[str]], known_statuses: dict[str, str]) -> str:
    reachable: set[str] = set()
    unknown = False
    for clazz in classes:
        if clazz not in known_statuses and clazz not in adjacency and clazz not in ROOTS:
            unknown = True
        reachable.update(root_reachability(clazz, adjacency, memo))
    if unknown and not reachable:
        return "EVENT_ROOT_UNKNOWN"
    if len(reachable) == 2:
        return "REACHES_BOTH"
    if "Q1656682" in reachable:
        return "REACHES_Q1656682"
    if "Q1190554" in reachable:
        return "REACHES_Q1190554"
    return "TERMINAL_NO_ROOT"


def passes_surface_filter(label: str) -> bool:
    leakage = re.compile(
        r"(?:[0-9]|\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\b|\b(?:ad|bc|bce|ce)\b)",
        re.IGNORECASE,
    )
    return bool(" ".join(label.strip().split())) and leakage.search(label) is None


def pair_events(events: list[dict[str, Any]]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    used: set[str] = set()
    for index, left in enumerate(events):
        if left["wikidata_item_id"] in used:
            continue
        for right in events[index + 1 :]:
            if right["wikidata_item_id"] in used:
                continue
            if right["p585_point_in_time_value"] == left["p585_point_in_time_value"]:
                continue
            used.update((left["wikidata_item_id"], right["wikidata_item_id"]))
            pairs.append((left["wikidata_item_id"], right["wikidata_item_id"]))
            break
    return pairs


def run() -> dict[str, Any]:
    entry_gate = verify_entry_gate()
    v8 = _v8_module()
    candidates = load_frozen_candidates(v8)
    confirmation_manifest = read_json(CONFIRMATION_MANIFEST_PATH)
    records = [parse_confirmation_identity(row["canonical_identity"]) for row in confirmation_manifest["records"]]
    qids = {row["wikidata_item_id"] for row in records}
    metadata, classes = load_cached_semantics(v8, candidates, qids)
    adjacency, known_statuses = load_ontology()
    closure_memo: dict[str, frozenset[str]] = {}
    seen_identities: Counter[str] = Counter(row["canonical_identity"] for row in records)
    stage_rows: list[dict[str, Any]] = []
    for row in records:
        qid = row["wikidata_item_id"]
        status = root_status(classes.get(qid, set()), adjacency, closure_memo, known_statuses)
        record = metadata.get(qid)
        exact_metadata = False
        unique_metadata = bool(record and len(record["labels"]) == 1 and len(record["records"]) == 1)
        if unique_metadata:
            exact_metadata = (row["accepted_date"], row["p585_point_in_time_value"], row["date_precision"], row["calendar_model"]) in record["records"]
        root_valid = status in {"REACHES_Q1656682", "REACHES_Q1190554", "REACHES_BOTH"}
        date_valid = root_valid and unique_metadata and exact_metadata and row["date_precision"] >= MIN_PRECISION and row["calendar_model"] == GREGORIAN_QID
        dedup_valid = date_valid and seen_identities[row["canonical_identity"]] == 1
        label = next(iter(record["labels"])) if unique_metadata else ""
        surface_pass = dedup_valid and passes_surface_filter(label)
        stage_rows.append({
            "canonical_identity": row["canonical_identity"],
            "wikidata_item_id": qid,
            "direct_p31_count": len(classes.get(qid, set())),
            "event_root_status": status,
            "metadata_unique": unique_metadata,
            "metadata_exact_match": exact_metadata,
            "date_valid_after_root": date_valid,
            "dedup_valid": dedup_valid,
            "surface_leakage_pass": surface_pass,
            "final_eligible": surface_pass,
        })
    eligible = [
        dict(row, p585_point_in_time_value=parsed["p585_point_in_time_value"])
        for row in stage_rows
        for parsed in [parse_confirmation_identity(row["canonical_identity"])]
        if row["final_eligible"]
    ]
    eligible.sort(key=lambda row: (row["p585_point_in_time_value"], row["wikidata_item_id"], row["canonical_identity"]))
    pairs = pair_events(eligible)
    counts = {
        "CONFIRMATION_TOTAL": len(records),
        "EVENT_ROOT_VALID": sum(row["event_root_status"] in {"REACHES_Q1656682", "REACHES_Q1190554", "REACHES_BOTH"} for row in stage_rows),
        "EVENT_ROOT_INVALID": sum(row["event_root_status"] == "TERMINAL_NO_ROOT" for row in stage_rows),
        "EVENT_ROOT_UNKNOWN": sum(row["event_root_status"] == "EVENT_ROOT_UNKNOWN" for row in stage_rows),
        "DATE_VALID_AFTER_ROOT": sum(row["date_valid_after_root"] for row in stage_rows),
        "DEDUP_VALID": sum(row["dedup_valid"] for row in stage_rows),
        "SURFACE_LEAKAGE_PASS": sum(row["surface_leakage_pass"] for row in stage_rows),
        "SURFACE_LEAKAGE_REJECT": sum(row["dedup_valid"] and not row["surface_leakage_pass"] for row in stage_rows),
        "FINAL_ELIGIBLE_EVENTS": len(eligible),
        "PAIRABLE_EVENTS": len(pairs) * 2,
        "TEMPORAL_FAMILIES_POSSIBLE": len(pairs),
    }
    rates = {
        "event_root_survival_rate": counts["EVENT_ROOT_VALID"] / counts["CONFIRMATION_TOTAL"],
        "dedup_survival_rate": counts["DEDUP_VALID"] / counts["DATE_VALID_AFTER_ROOT"] if counts["DATE_VALID_AFTER_ROOT"] else 0.0,
        "surface_leakage_survival_rate": counts["SURFACE_LEAKAGE_PASS"] / counts["DEDUP_VALID"] if counts["DEDUP_VALID"] else 0.0,
        "final_eligibility_rate": counts["FINAL_ELIGIBLE_EVENTS"] / counts["CONFIRMATION_TOTAL"],
    }
    losses = {
        "ONTOLOGY_ROOT": counts["EVENT_ROOT_INVALID"] + counts["EVENT_ROOT_UNKNOWN"],
        "SURFACE_LEAKAGE": counts["SURFACE_LEAKAGE_REJECT"],
        "PAIRING": counts["FINAL_ELIGIBLE_EVENTS"] - counts["PAIRABLE_EVENTS"],
    }
    dominant = max(losses, key=losses.get) if any(losses.values()) else "OTHER"
    if dominant == "PAIRING" and losses[dominant] <= 0:
        dominant = "OTHER"
    if counts["EVENT_ROOT_UNKNOWN"] != 0:
        raise RuntimeError("TEMP_FEAS_002R_EVENT_ROOT_UNKNOWN_NONZERO")
    if counts["FINAL_ELIGIBLE_EVENTS"] >= 500 and counts["TEMPORAL_FAMILIES_POSSIBLE"] >= 220:
        confirmation_status = "SUPPORTED_WITH_RESERVE"
        confirmed = True
    elif counts["FINAL_ELIGIBLE_EVENTS"] >= 440 and counts["TEMPORAL_FAMILIES_POSSIBLE"] >= 220:
        confirmation_status = "SUPPORTED_MINIMUM"
        confirmed = True
    else:
        confirmation_status = "INSUFFICIENT_EXISTING_POOL"
        confirmed = False
    funnel = {
        "task_id": "PA-EXT-A-TEMP-FEAS-002R",
        "rule_id": "TEMPORAL_EVENT_LIKE_V1",
        "proposal_sha256": EXPECTED_PROPOSAL_SHA,
        "confirmation_manifest_sha256": EXPECTED_CONFIRMATION_SHA,
        "ontology_snapshot_authority_sha256": EXPECTED_ONTOLOGY_AUTHORITY_SHA,
        "counts": counts,
        "survival_rates": rates,
        "dominant_bottleneck": dominant,
        "bottleneck_losses": losses,
        "pairing_rule_applied": "sorted eligible events, no event reuse, next unused event with a different normalized timeValue",
    }
    confirmation = {
        "task_id": "PA-EXT-A-TEMP-FEAS-002R",
        "status": "CONFIRMATION_COMPLETED",
        "confirmation_exposure": True,
        "entry_gate": entry_gate,
        "frozen_rule_id": "TEMPORAL_EVENT_LIKE_V1",
        "confirmation_total": len(records),
        "records": stage_rows,
        "event_root_status_counts": dict(Counter(row["event_root_status"] for row in stage_rows)),
        "final_eligible_identities": [row["canonical_identity"] for row in eligible],
        "pair_ids": [list(pair) for pair in pairs],
        "network_accessed": False,
        "model_inference_performed": False,
        "formal_panel_accessed": False,
    }
    funnel_sha = write_hashed_json(OUTPUT_DIR / "temp_feas_002r_funnel.json", funnel)
    confirmation_sha = write_hashed_json(OUTPUT_DIR / "temp_feas_002r_confirmation.json", confirmation)
    report = {
        "task_id": "PA-EXT-A-TEMP-FEAS-002R",
        "status": confirmation_status,
        "rule_confirmed": confirmed,
        "proposal_sha256": EXPECTED_PROPOSAL_SHA,
        "confirmation_manifest_sha256": EXPECTED_CONFIRMATION_SHA,
        "source_pool_manifest_sha256": EXPECTED_POOL_SHA,
        "ontology_snapshot_authority_sha256": EXPECTED_ONTOLOGY_AUTHORITY_SHA,
        "ontology_closure_unresolved_seeds": 0,
        "confirmation_artifact_sha256": confirmation_sha,
        "funnel_artifact_sha256": funnel_sha,
        "counts": counts,
        "survival_rates": rates,
        "dominant_bottleneck": dominant,
        "no_rule_redesign": True,
        "no_canonical_temporal_220_created": True,
        "required_flags": {
            "PA_EXT_A_TEMP_FEAS_002R_COMPLETE": True,
            "PA_EXT_A_TEMP_RULE_SHA_VALID": True,
            "PA_EXT_A_CONFIRMATION_MANIFEST_SHA_VALID": True,
            "PA_EXT_A_ONTOLOGY_SNAPSHOT_SHA_VALID": True,
            "PA_EXT_A_ONTOLOGY_CLOSURE_COMPLETE": True,
            "PA_EXT_A_EVENT_ROOT_UNKNOWN": 0,
            "PA_EXT_A_CONFIRMATION_SEMANTICS_ACCESSED": True,
            "PA_EXT_A_CONFIRMATION_STATUS": confirmation_status,
            "PA_EXT_A_TEMP_RULE_CONFIRMED": confirmed,
            "PA_EXT_A_TEMPORAL_220_CREATED": False,
            "PA_EXT_A_FORMAL_PANEL_ACCESSED": False,
            "PA_EXT_A_FORMAL_INFERENCE_PERFORMED": False,
            "PA_EXT_A_FORMAL_SCIENTIFIC_OUTCOME_CREATED": False,
            "PA_EXT_A_V8_LINEAGE_MODIFIED": False,
            "PA_EXT_A_NETWORK_ACCESSED": False,
        },
    }
    report_sha = write_hashed_json(OUTPUT_DIR / "temp_feas_002r_report.json", report)
    return {"confirmation": confirmation, "funnel": funnel, "report": report, "artifact_shas": {"confirmation": confirmation_sha, "funnel": funnel_sha, "report": report_sha}}


if __name__ == "__main__":
    result = run()
    print("STATUS=TEMP_FEAS_002R_CONFIRMATION_COMPLETE")
    print(f"CONFIRMATION_TOTAL={result['funnel']['counts']['CONFIRMATION_TOTAL']}")
    print(f"EVENT_ROOT_VALID={result['funnel']['counts']['EVENT_ROOT_VALID']}")
    print(f"EVENT_ROOT_INVALID={result['funnel']['counts']['EVENT_ROOT_INVALID']}")
    print(f"EVENT_ROOT_UNKNOWN={result['funnel']['counts']['EVENT_ROOT_UNKNOWN']}")
    print(f"SURFACE_LEAKAGE_PASS={result['funnel']['counts']['SURFACE_LEAKAGE_PASS']}")
    print(f"FINAL_ELIGIBLE_EVENTS={result['funnel']['counts']['FINAL_ELIGIBLE_EVENTS']}")
    print(f"PAIRABLE_EVENTS={result['funnel']['counts']['PAIRABLE_EVENTS']}")
    print(f"TEMPORAL_FAMILIES_POSSIBLE={result['funnel']['counts']['TEMPORAL_FAMILIES_POSSIBLE']}")
    print(f"CONFIRMATION_STATUS={result['report']['status']}")
    print(f"PA_EXT_A_TEMP_RULE_CONFIRMED={result['report']['rule_confirmed']}")
    print(f"DOMINANT_BOTTLENECK={result['report']['dominant_bottleneck']}")
    print("NETWORK_ACCESSED=false")
    print("MODEL_INFERENCE=false")
