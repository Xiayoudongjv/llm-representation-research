"""Build the TEMP-FEAS-002E auxiliary Wikidata P279 ontology snapshot.

Only the official Wikidata MediaWiki Entity API is used for missing ontology
nodes.  This module never reads labels, descriptions, dates, or candidate
split assignments, and it never writes into the V8 raw lineage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXP_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = EXP_DIR / "data" / "raw" / "wikidata_v8"
OUTPUT_DIR = EXP_DIR / "engineering" / "temp_feas_002e"
V8_AUTHORITY = EXP_DIR / "paper_a_ext_a_temporal_asset_source_v8.json"
V8_RULE = EXP_DIR / "v7_main_view_rule.json"
API_ENDPOINT = "https://www.wikidata.org/w/api.php"
ROOTS = ("Q1656682", "Q1190554")
SEED_RULE_ID = "PA_EXT_A_TEMP_FEAS_002E_SEED_V1"
SNAPSHOT_VERSION = "TEMP_FEAS_002E_ONTOLOGY_SNAPSHOT_V1"
MAX_BATCH_SIZE = 50
MAX_RETRIES = 3
RETRY_DELAYS_SECONDS = (1.0, 2.0, 4.0)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def content_hash(value: dict[str, Any], field: str) -> str:
    body = dict(value)
    body.pop(field, None)
    return sha256_bytes(canonical_json(body))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_v8_module() -> Any:
    sys.path.insert(0, str(EXP_DIR))
    import acquire_wikidata_temporal_v8 as v8  # type: ignore[import-not-found]

    return v8


def derive_seed_qids(v8: Any) -> list[str]:
    """Derive the seed from cached class infrastructure only."""

    checkpoint = json.loads((RAW_DIR / "acquisition_checkpoint.json").read_text(encoding="utf-8"))
    bounded = dict(checkpoint)
    bounded["candidate_page_offsets_verified"] = [
        int(value) for value in checkpoint["candidate_page_offsets_verified"]
        if int(value) < int(checkpoint["next_candidate_offset"]) - v8.PAGE_SIZE
    ]
    candidates = v8._parse_candidates(v8._load_candidate_payloads(bounded))
    seed: set[str] = set()
    for start in range(0, len(candidates), v8.METADATA_BATCH_SIZE):
        qids = [row["wikidata_item_id"] for row in candidates[start : start + v8.METADATA_BATCH_SIZE]]
        identity = f"batch_{start:08d}"
        query = v8._class_query(qids)
        path = RAW_DIR / f"class_chunk_{identity}_{v8.query_sha256(query)[:16]}.json"
        parsed = v8._parse_classes(json.loads(path.read_text(encoding="utf-8")))
        seed.update(clazz for values in parsed.values() for clazz in values)
    return sorted(seed)


def load_cached_edges(v8: Any) -> dict[str, set[str]]:
    """Load only direct P279 edges from the existing V8 parent artifacts."""

    edges: dict[str, set[str]] = defaultdict(set)
    for path in sorted(RAW_DIR.glob("parent_chunk_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for binding in payload.get("results", {}).get("bindings", []):
            source = binding.get("class", {}).get("value", "").rsplit("/", 1)[-1]
            parent = binding.get("parent", {}).get("value", "").rsplit("/", 1)[-1]
            if source.startswith("Q") and parent.startswith("Q"):
                edges[source].add(parent)
    return {source: set(sorted(parents)) for source, parents in edges.items()}


def seed_manifest(seed_qids: list[str]) -> dict[str, Any]:
    value = {
        "task_id": "PA-EXT-A-TEMP-FEAS-002E",
        "schema_version": "1.0.0",
        "snapshot_version": SNAPSHOT_VERSION,
        "seed_rule_id": SEED_RULE_ID,
        "seed_source": "union of direct P31 class QIDs in cached V8 class infrastructure for the frozen 3550 date-valid pool",
        "seed_depends_on_design_or_confirmation_outcome": False,
        "v8_authority_sha256": sha256_file(V8_AUTHORITY),
        "v8_rule_sha256": sha256_file(V8_RULE),
        "seed_count": len(seed_qids),
        "seed_qids": seed_qids,
    }
    value["seed_manifest_sha256"] = content_hash(value, "seed_manifest_sha256")
    return value


def truthy_p279(entity: dict[str, Any]) -> list[str]:
    """Extract direct truthy P279 item targets, excluding deprecated claims."""

    statements = entity.get("claims", {}).get("P279", [])
    usable = [statement for statement in statements if statement.get("rank") != "deprecated"]
    preferred = [statement for statement in usable if statement.get("rank") == "preferred"]
    selected = preferred if preferred else [statement for statement in usable if statement.get("rank") == "normal"]
    parents: set[str] = set()
    for statement in selected:
        mainsnak = statement.get("mainsnak", {})
        if mainsnak.get("snaktype") != "value":
            continue
        value = mainsnak.get("datavalue", {}).get("value", {})
        qid = value.get("id") if isinstance(value, dict) else None
        if isinstance(qid, str) and qid.startswith("Q"):
            parents.add(qid)
    return sorted(parents)


def _api_url(qids: list[str]) -> str:
    params = {
        "action": "wbgetentities",
        "format": "json",
        "formatversion": "2",
        "ids": "|".join(qids),
        "props": "info|claims",
    }
    return API_ENDPOINT + "?" + urllib.parse.urlencode(params)


def fetch_batch(qids: list[str]) -> tuple[bytes, dict[str, Any]]:
    """Fetch one deterministic <=50-QID API batch with bounded retries."""

    if not qids or len(qids) > MAX_BATCH_SIZE or qids != sorted(set(qids)):
        raise ValueError("invalid deterministic API batch")
    request = urllib.request.Request(
        _api_url(qids),
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "PA-EXT-A-TEMP-FEAS-002E/1.0"},
    )
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read()
            parsed = json.loads(raw.decode("utf-8"))
            if not isinstance(parsed.get("entities"), dict):
                raise RuntimeError("WIKIDATA_API_ENTITIES_MISSING")
            return raw, parsed
        except Exception as exc:  # bounded retry wrapper for network/API failures
            last_error = exc
            if attempt + 1 == MAX_RETRIES:
                break
            time.sleep(RETRY_DELAYS_SECONDS[attempt])
    raise RuntimeError(f"WIKIDATA_API_FETCH_FAILED:{last_error}")


def _entity_record(entity: dict[str, Any], requested_qid: str, batch_id: str, raw_sha: str, timestamp: str) -> dict[str, Any]:
    resolved_qid = entity.get("resolved_qid") or entity.get("id")
    if not isinstance(resolved_qid, str) or not resolved_qid.startswith("Q"):
        raise RuntimeError("WIKIDATA_API_INVALID_QID")
    allowed_top_level = {
        "id", "pageid", "ns", "title", "lastrevid", "claims", "missing", "modified", "type", "redirects",
        "qid", "resolved_qid", "direct_p279_qids",
    }
    if set(entity) - allowed_top_level:
        raise RuntimeError("WIKIDATA_API_NON_ONTOLOGY_FIELDS_PRESENT")
    return {
        "qid": requested_qid,
        "resolved_qid": resolved_qid,
        "lastrevid": entity.get("lastrevid"),
        "retrieval_timestamp": timestamp,
        "batch_id": batch_id,
        "raw_response_sha256": raw_sha,
        "direct_p279_qids": sorted(entity["direct_p279_qids"]) if "direct_p279_qids" in entity else truthy_p279(entity),
        "source": "WIKIDATA_OFFICIAL_ENTITY_API",
    }


def _save_batch(
    output_dir: Path,
    batch_id: str,
    raw: bytes,
    raw_response_sha256: str,
    retrieval_timestamp: str,
    requested_qids: list[str],
) -> Path:
    batch_dir = output_dir / "entity_api_batches"
    batch_dir.mkdir(parents=True, exist_ok=True)
    path = batch_dir / f"{batch_id}_{sha256_bytes(raw)[:16]}.json"
    if path.exists() and path.read_bytes() != raw:
        raise RuntimeError("WIKIDATA_BATCH_HASH_COLLISION")
    path.write_bytes(raw)
    path.with_suffix(".meta.json").write_text(
        json.dumps(
            {
                "batch_id": batch_id,
                "requested_qids": requested_qids,
                "raw_response_sha256": raw_response_sha256,
                "retrieval_timestamp": retrieval_timestamp,
                "snapshot_fields": ["qid", "resolved_qid", "lastrevid", "redirects", "direct_p279_qids"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _load_existing_batch(output_dir: Path, batch_id: str) -> tuple[bytes, dict[str, Any], Path, dict[str, Any]] | None:
    """Resume from a verified successful batch without refetching it."""

    matches = sorted(
        path
        for path in (output_dir / "entity_api_batches").glob(f"{batch_id}_*.json")
        if not path.name.endswith(".meta.json")
    )
    if not matches:
        return None
    if len(matches) != 1:
        raise RuntimeError(f"WIKIDATA_BATCH_ID_AMBIGUOUS_{batch_id}")
    path = matches[0]
    raw = path.read_bytes()
    expected_prefix = path.stem.rsplit("_", 1)[-1]
    if not sha256_bytes(raw).startswith(expected_prefix):
        raise RuntimeError(f"WIKIDATA_BATCH_HASH_MISMATCH_{batch_id}")
    parsed = json.loads(raw.decode("utf-8"))
    meta_path = path.with_suffix(".meta.json")
    metadata = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {
        "raw_response_sha256": None,
        "retrieval_timestamp": None,
    }
    return raw, parsed, path, metadata


def _minimal_entity(requested_qid: str, entity: dict[str, Any]) -> dict[str, Any]:
    """Retain only ontology fields; never persist the full API claims map."""

    result: dict[str, Any] = {
        "qid": requested_qid,
        "resolved_qid": entity.get("id"),
        "lastrevid": entity.get("lastrevid"),
        "direct_p279_qids": truthy_p279(entity),
    }
    if isinstance(entity.get("redirects"), dict):
        result["redirects"] = entity["redirects"]
    if entity.get("missing") is True:
        result["missing"] = True
    return result


def _minimal_payload(requested_qids: list[str], parsed: dict[str, Any]) -> dict[str, Any]:
    entities = parsed.get("entities", {})
    return {
        "snapshot_fields": ["qid", "resolved_qid", "lastrevid", "redirects", "direct_p279_qids"],
        "entities": {
            qid: _minimal_entity(qid, entities.get(qid, {"id": qid, "missing": True, "claims": {}}))
            for qid in requested_qids
        },
    }


def sanitize_existing_batches(output_dir: Path) -> None:
    """Convert any pre-existing full API responses to safe minimal snapshots."""

    batch_dir = output_dir / "entity_api_batches"
    revision_path = output_dir / "ontology_entity_revisions.json"
    prior = {}
    if revision_path.exists():
        prior = {record["qid"]: record for record in json.loads(revision_path.read_text(encoding="utf-8")).get("entities", [])}
    for path in sorted(batch_dir.glob("entity_batch_*.json")):
        if path.name.endswith(".meta.json"):
            continue
        parsed = json.loads(path.read_text(encoding="utf-8"))
        entities = parsed.get("entities", {})
        if not entities:
            continue
        if all("direct_p279_qids" in entity for entity in entities.values()):
            continue
        requested_qids = sorted(entities)
        minimal = _minimal_payload(requested_qids, parsed)
        minimal_raw = (json.dumps(minimal, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        raw_response_sha = None
        timestamps = []
        for qid in requested_qids:
            record = prior.get(qid)
            if record:
                raw_response_sha = record["raw_response_sha256"]
                timestamps.append(record["retrieval_timestamp"])
        if raw_response_sha is None or not timestamps:
            raise RuntimeError(f"WIKIDATA_UNSAFE_BATCH_METADATA_MISSING_{path.name}")
        replacement = _save_batch(output_dir, path.stem, minimal_raw, raw_response_sha, sorted(timestamps)[0], requested_qids)
        path.unlink()
        old_meta = path.with_suffix(".meta.json")
        if old_meta.exists():
            old_meta.unlink()
        if replacement != path:
            continue


def fetch_recursive(seed_qids: list[str], cached_edges: dict[str, set[str]], output_dir: Path) -> tuple[dict[str, set[str]], dict[str, dict[str, Any]], list[Path]]:
    """Resolve every reachable ontology node without candidate-level fields."""

    edges = {source: set(parents) for source, parents in cached_edges.items()}
    revisions: dict[str, dict[str, Any]] = {}
    raw_paths: list[Path] = []
    prior_revisions: dict[str, dict[str, Any]] = {}
    prior_path = output_dir / "ontology_entity_revisions.json"
    if prior_path.exists():
        prior_doc = json.loads(prior_path.read_text(encoding="utf-8"))
        prior_revisions = {record["qid"]: record for record in prior_doc.get("entities", [])}
    pending = sorted(set(seed_qids))
    processed: set[str] = set()
    batch_index = 0
    while pending:
        current = [qid for qid in pending if qid not in processed and qid not in ROOTS]
        pending = []
        unknown = sorted(qid for qid in current if qid not in edges)
        for start in range(0, len(unknown), MAX_BATCH_SIZE):
            batch = unknown[start : start + MAX_BATCH_SIZE]
            batch_id = f"entity_batch_{batch_index:04d}"
            existing = _load_existing_batch(output_dir, batch_id)
            if existing is None:
                raw_api, parsed_api = fetch_batch(batch)
                raw_response_sha = sha256_bytes(raw_api)
                timestamp = now_utc()
                minimal = _minimal_payload(batch, parsed_api)
                minimal_raw = (json.dumps(minimal, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
                raw_paths.append(_save_batch(output_dir, batch_id, minimal_raw, raw_response_sha, timestamp, batch))
                parsed = minimal
                raw = minimal_raw
                batch_metadata = {"raw_response_sha256": raw_response_sha, "retrieval_timestamp": timestamp}
            else:
                raw, parsed, existing_path, batch_metadata = existing
                raw_paths.append(existing_path)
            raw_sha = batch_metadata.get("raw_response_sha256") or sha256_bytes(raw)
            timestamp = batch_metadata.get("retrieval_timestamp") or now_utc()
            for qid in batch:
                entity = parsed.get("entities", {}).get(qid, {"id": qid, "missing": True, "claims": {}})
                current_record = _entity_record(entity, qid, batch_id, raw_sha, timestamp)
                previous_record = prior_revisions.get(qid)
                if previous_record is not None:
                    comparable = dict(current_record)
                    comparable.pop("retrieval_timestamp", None)
                    previous_comparable = dict(previous_record)
                    previous_comparable.pop("retrieval_timestamp", None)
                    previous_comparable.setdefault("resolved_qid", previous_comparable["qid"])
                    if comparable != previous_comparable:
                        raise RuntimeError(f"WIKIDATA_PRIOR_ENTITY_RECORD_MISMATCH_{qid}")
                    record = dict(previous_record)
                    record.setdefault("resolved_qid", record["qid"])
                else:
                    record = current_record
                revisions[qid] = record
                edges[qid] = set(record["direct_p279_qids"])
            batch_index += 1
        for qid in current:
            if qid in processed or qid in ROOTS:
                continue
            processed.add(qid)
            pending.extend(sorted(edges.get(qid, set()) - processed - set(ROOTS)))
        pending = sorted(set(pending))
    return edges, revisions, raw_paths


def classify_seed(seed: str, edges: dict[str, set[str]]) -> str:
    roots: set[str] = set()
    terminal = False
    cycle = False
    unresolved = False

    def visit(node: str, path: tuple[str, ...]) -> None:
        nonlocal terminal, cycle, unresolved
        if node == ROOTS[0]:
            roots.add(ROOTS[0])
            return
        if node == ROOTS[1]:
            roots.add(ROOTS[1])
            return
        if node in path:
            cycle = True
            return
        if node not in edges:
            unresolved = True
            return
        parents = sorted(edges[node])
        if not parents:
            terminal = True
            return
        for parent in parents:
            visit(parent, path + (node,))

    visit(seed, ())
    if unresolved:
        return "UNRESOLVED"
    if roots == set(ROOTS):
        return "REACHES_BOTH"
    if ROOTS[0] in roots:
        return "REACHES_Q1656682"
    if ROOTS[1] in roots:
        return "REACHES_Q1190554"
    if cycle:
        return "CYCLE_NO_ROOT"
    if terminal:
        return "TERMINAL_NO_ROOT"
    return "UNRESOLVED"


def closure_status(seed_qids: list[str], edges: dict[str, set[str]]) -> dict[str, str]:
    return {qid: classify_seed(qid, edges) for qid in seed_qids}


def build(output_dir: Path = OUTPUT_DIR) -> dict[str, Any]:
    v8 = _load_v8_module()
    output_dir.mkdir(parents=True, exist_ok=True)
    sanitize_existing_batches(output_dir)
    seeds = derive_seed_qids(v8)
    seed = seed_manifest(seeds)
    write_json(output_dir / "ontology_seed_manifest.json", seed)
    cached_edges = load_cached_edges(v8)
    edges, revisions, raw_paths = fetch_recursive(seeds, cached_edges, output_dir)
    prior_revisions_path = output_dir / "ontology_entity_revisions.json"
    if prior_revisions_path.exists():
        prior_revisions = {
            record["qid"]: record
            for record in json.loads(prior_revisions_path.read_text(encoding="utf-8")).get("entities", [])
        }
        for qid in set(revisions) & set(prior_revisions):
            revisions[qid] = prior_revisions[qid]
    statuses = closure_status(seeds, edges)
    unresolved = sum(status == "UNRESOLVED" for status in statuses.values())
    direct_edges = {
        "task_id": "PA-EXT-A-TEMP-FEAS-002E",
        "schema_version": "1.0.0",
        "roots": list(ROOTS),
        "only_predicate": "P279",
        "edges": [{"source_qid": source, "direct_p279_qids": sorted(edges[source])} for source in sorted(edges)],
    }
    revisions_doc = {
        "task_id": "PA-EXT-A-TEMP-FEAS-002E",
        "schema_version": "1.0.0",
        "source": "WIKIDATA_OFFICIAL_ENTITY_API",
        "entities": [revisions[qid] for qid in sorted(revisions)],
    }
    closure_doc = {
        "task_id": "PA-EXT-A-TEMP-FEAS-002E",
        "schema_version": "1.0.0",
        "roots": list(ROOTS),
        "ontology_nodes_total": len(edges),
        "direct_edges_total": sum(len(values) for values in edges.values()),
        "network_entities_fetched": len(revisions),
        "root_reachable_seed_count": sum(status.startswith("REACHES_") for status in statuses.values()),
        "terminal_nonroot_seed_count": sum(status == "TERMINAL_NO_ROOT" for status in statuses.values()),
        "cycle_seed_count": sum(status == "CYCLE_NO_ROOT" for status in statuses.values()),
        "unresolved_seed_count": unresolved,
        "seed_statuses": statuses,
        "algorithm": "deterministic sorted frontier, bounded API batches <=50, cycle-aware local reachability",
    }
    for path, value, field in [
        ("ontology_direct_edges.json", direct_edges, None),
        ("ontology_entity_revisions.json", revisions_doc, None),
        ("ontology_closure_status.json", closure_doc, None),
    ]:
        if field is None:
            value["artifact_sha256"] = content_hash(value, "artifact_sha256")
        write_json(output_dir / path, value)
    snapshot_inputs = {
        "snapshot_version": SNAPSHOT_VERSION,
        "frozen_roots": list(ROOTS),
        "traversal_algorithm": closure_doc["algorithm"],
        "seed_manifest_sha256": seed["seed_manifest_sha256"],
        "direct_edges_sha256": json.loads((output_dir / "ontology_direct_edges.json").read_text(encoding="utf8"))["artifact_sha256"],
        "entity_revisions_sha256": json.loads((output_dir / "ontology_entity_revisions.json").read_text(encoding="utf8"))["artifact_sha256"],
        "closure_status_sha256": json.loads((output_dir / "ontology_closure_status.json").read_text(encoding="utf8"))["artifact_sha256"],
    }
    snapshot_authority_sha = sha256_bytes(canonical_json(snapshot_inputs))
    report = {
        "task_id": "PA-EXT-A-TEMP-FEAS-002E",
        "status": "TEMP_FEAS_002E_ONTOLOGY_CLOSURE_COMPLETE" if unresolved == 0 else "TEMP_FEAS_002E_BLOCKED_UNRESOLVED_ONTOLOGY",
        "snapshot_version": SNAPSHOT_VERSION,
        "seed_count": len(seeds),
        "seed_manifest_sha256": seed["seed_manifest_sha256"],
        "ontology_nodes_total": closure_doc["ontology_nodes_total"],
        "direct_edges_total": closure_doc["direct_edges_total"],
        "network_entities_fetched": closure_doc["network_entities_fetched"],
        "root_reachable_seed_count": closure_doc["root_reachable_seed_count"],
        "terminal_nonroot_seed_count": closure_doc["terminal_nonroot_seed_count"],
        "cycle_seed_count": closure_doc["cycle_seed_count"],
        "unresolved_seed_count": unresolved,
        "snapshot_authority_sha256": snapshot_authority_sha,
        "official_source": API_ENDPOINT,
        "v8_lineage_modified": False,
        "temporal_rule_changed": False,
        "source_confirmation_eligibility_computed": False,
        "source_confirmation_yield_computed": False,
        "source_confirmation_labels_accessed": False,
        "source_confirmation_dates_accessed_for_analysis": False,
        "source_confirmation_leakage_computed": False,
        "temporal_220_created": False,
        "formal_panel_accessed": False,
        "formal_inference_performed": False,
        "formal_scientific_outcome_created": False,
        "raw_api_batch_count": len(raw_paths),
        "required_flags": {
            "PA_EXT_A_TEMP_FEAS_002E_COMPLETE": unresolved == 0,
            "PA_EXT_A_ONTOLOGY_SEED_FROZEN": True,
            "PA_EXT_A_ONTOLOGY_CLOSURE_COMPLETE": unresolved == 0,
            "PA_EXT_A_ONTOLOGY_UNRESOLVED_SEEDS": unresolved,
            "PA_EXT_A_AUX_ONTOLOGY_SOURCE": "WIKIDATA_OFFICIAL_ENTITY_API",
            "PA_EXT_A_TEMP_RULE_CHANGED": False,
            "PA_EXT_A_CONFIRMATION_ELIGIBILITY_COMPUTED": False,
            "PA_EXT_A_CONFIRMATION_YIELD_COMPUTED": False,
            "PA_EXT_A_CONFIRMATION_SEMANTIC_OUTCOME_EXPOSED": False,
            "PA_EXT_A_TEMPORAL_220_CREATED": False,
            "PA_EXT_A_FORMAL_PANEL_ACCESSED": False,
            "PA_EXT_A_FORMAL_INFERENCE_PERFORMED": False,
            "PA_EXT_A_FORMAL_SCIENTIFIC_OUTCOME_CREATED": False,
            "PA_EXT_A_V8_LINEAGE_MODIFIED": False,
        },
    }
    report["artifact_sha256"] = content_hash(report, "artifact_sha256")
    write_json(output_dir / "temp_feas_002e_report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build TEMP-FEAS-002E ontology-only snapshot")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args(argv)
    report = build(args.output_dir)
    print(f"STATUS={report['status']}")
    print(f"SEED_COUNT={report['seed_count']}")
    print(f"NETWORK_ENTITIES_FETCHED={report['network_entities_fetched']}")
    print(f"UNRESOLVED_SEEDS={report['unresolved_seed_count']}")
    print(f"SNAPSHOT_AUTHORITY_SHA256={report['snapshot_authority_sha256']}")
    print("SOURCE_CONFIRMATION_ELIGIBILITY_COMPUTED=false")
    print("SOURCE_CONFIRMATION_YIELD_COMPUTED=false")
    print("V8_LINEAGE_MODIFIED=false")
    return 0 if report["unresolved_seed_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
