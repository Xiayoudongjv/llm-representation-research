"""Production-ready TEMPORAL_SOURCE_V2 acquisition core.

The formal ``--run`` path is intentionally not invoked by repository
qualification tasks.  Network access is isolated in :class:`QLeverClient`;
all selection, checkpoint, pairing, and publication logic is deterministic and
testable with offline fixtures.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable


EXP_DIR = Path(__file__).resolve().parent
PROTOCOL_PATH = EXP_DIR / "engineering" / "temp_feas_v2" / "temporal_source_v2_protocol.json"
V7_RULE_PATH = EXP_DIR / "v7_main_view_rule.json"
RUNTIME_DIR = EXP_DIR / "data" / "temporal_source_v2_runtime"
CANONICAL_DIR = EXP_DIR / "data" / "wikidata_temporal_source_v2"
DEFAULT_CHECKPOINT_PATH = RUNTIME_DIR / "checkpoint.json"
QLEVER_ENDPOINT = "https://qlever.dev/api/wikidata"
GRAPH_SCOPE = "UNIFIED"
MAIN_VIEW_RULE_SHA256 = "ece32b16462f6abc42d6cba0b4a5a433fbfdacf51278ea46d7bf1f8d22adec05"
PROTOCOL_SHA256 = "5018718739045b25514c8e94ede7e7ba6a99faa56b43c2156d27fbb97cfe2b6b"
ROOTS = ("Q1190554", "Q1656682")
GREGORIAN_QID = "Q1985727"
MIN_PRECISION = 11
PAGE_SIZE = 100
TARGET_EVENTS = 440
TARGET_FAMILIES = 220
RESERVE_EVENTS = 600
CLASS_CAP = 44
MAX_RETRIES = 3
DATE_RE = re.compile(
    r"(?:"
    r"(?<!\d)\d{4}(?!\d)|"
    r"(?<!\d)\d{1,2}[/-]\d{1,2}[/-]\d{2,4}(?!\d)|"
    r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:,\s*)?\d{4}\b|"
    r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}\b|"
    r"\b\d{1,4}\s*(?:bce|bc|ce|ad)\b"
    r")",
    re.IGNORECASE,
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_bytes(path, (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def load_protocol() -> dict[str, Any]:
    if sha256_file(PROTOCOL_PATH) != PROTOCOL_SHA256:
        raise RuntimeError("TEMPORAL_SOURCE_V2_PROTOCOL_SHA_MISMATCH")
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    if protocol.get("protocol_status") != "FROZEN_BEFORE_FRESH_ACQUISITION":
        raise RuntimeError("TEMPORAL_SOURCE_V2_PROTOCOL_NOT_FROZEN")
    if protocol.get("required_flags", {}).get("TEMPORAL_SOURCE_V2_DATA_ACCESSED") is not False:
        raise RuntimeError("TEMPORAL_SOURCE_V2_PROTOCOL_DATA_ALREADY_ACCESSED")
    return protocol


def main_view_filter() -> str:
    """Reuse the frozen V7 main-view implementation without changing it."""
    import sys

    sys.path.insert(0, str(EXP_DIR))
    from qlever_v7_main_view import main_view_filter as frozen_filter

    return frozen_filter()


def event_page_query(limit: int, offset: int) -> str:
    if limit <= 0 or offset < 0:
        raise ValueError("limit must be positive and offset must be non-negative")
    return f"""PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?item ?class ?label WHERE {{
  ?item wdt:P31 ?class .
  ?class wdt:P279* ?root .
  VALUES ?root {{ wd:Q1190554 wd:Q1656682 }}
  ?item rdfs:label ?label .
  FILTER(lang(?label)="en")
  {main_view_filter()}
}}
ORDER BY ASC(?item) ASC(?class)
LIMIT {limit}
OFFSET {offset}"""


def time_metadata_query(qids: Iterable[str]) -> str:
    values = " ".join(f"wd:{qid}" for qid in sorted(set(qids)))
    return f"""PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX ps: <http://www.wikidata.org/prop/statement/>
PREFIX psv: <http://www.wikidata.org/prop/statement/value/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX wikibase: <http://wikiba.se/ontology#>
SELECT ?item ?label ?property ?timeValue ?precision ?calendar WHERE {{
  VALUES ?item {{ {values} }}
  ?item rdfs:label ?label . FILTER(lang(?label)="en")
  {{
    BIND("P580" AS ?property)
    ?item p:P580 ?statement . ?statement ps:P580 ?date ;
      psv:P580 ?valueNode .
  }} UNION {{
    BIND("P585" AS ?property)
    ?item p:P585 ?statement . ?statement ps:P585 ?date ;
      psv:P585 ?valueNode .
  }}
  ?valueNode wikibase:timeValue ?timeValue ;
    wikibase:timePrecision ?precision ;
    wikibase:timeCalendarModel ?calendar .
}}"""


def parent_query(qids: Iterable[str]) -> str:
    values = " ".join(f"wd:{qid}" for qid in sorted(set(qids)))
    return f"""PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
SELECT ?class ?parent WHERE {{
  VALUES ?class {{ {values} }}
  ?class wdt:P279 ?parent .
}}"""


class QLeverClient:
    """Small bounded client; it never retries beyond the frozen limit."""

    def __init__(self, endpoint: str = QLEVER_ENDPOINT, request: Callable[[str], tuple[int, dict[str, Any]]] | None = None):
        self.endpoint = endpoint
        self._request_override = request

    def request(self, query: str) -> tuple[int, dict[str, Any]]:
        if self._request_override is not None:
            return self._request_override(query)
        body = urllib.parse.urlencode({"query": query}).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=body,
            method="POST",
            headers={"Accept": "application/sparql-results+json", "Content-Type": "application/x-www-form-urlencoded", "User-Agent": "PA-EXT-A-TEMP-V2/1.0"},
        )
        last: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    return int(response.status), json.loads(response.read().decode("utf-8"))
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last = exc
                if attempt == MAX_RETRIES:
                    break
                time.sleep(float(2 ** (attempt - 1)))
        raise RuntimeError(f"V2_QLEVER_REQUEST_FAILED:{last}")

    def preflight(self) -> dict[str, Any]:
        status, payload = self.request("SELECT * WHERE { BIND(1 AS ?health) } LIMIT 1")
        if status != 200:
            raise RuntimeError("TEMPORAL_SOURCE_V2_BACKEND_HEALTH_FAILED")
        if self.endpoint != QLEVER_ENDPOINT:
            raise RuntimeError("TEMPORAL_SOURCE_V2_ENDPOINT_IDENTITY_FAILED")
        if sha256_file(V7_RULE_PATH) != MAIN_VIEW_RULE_SHA256:
            raise RuntimeError("TEMPORAL_SOURCE_V2_MAIN_VIEW_RULE_SHA_MISMATCH")
        return {"status": status, "endpoint": self.endpoint, "graph_scope": GRAPH_SCOPE, "main_view_rule_sha256": MAIN_VIEW_RULE_SHA256, "health_payload_keys": sorted(payload.keys())}

    def fetch_event_page(self, limit: int, offset: int) -> dict[str, Any]:
        status, payload = self.request(event_page_query(limit, offset))
        if status != 200:
            raise RuntimeError("TEMPORAL_SOURCE_V2_EVENT_PAGE_FAILED")
        return payload

    def fetch_time_metadata(self, qids: Iterable[str]) -> dict[str, Any]:
        status, payload = self.request(time_metadata_query(qids))
        if status != 200:
            raise RuntimeError("TEMPORAL_SOURCE_V2_TIME_METADATA_FAILED")
        return payload

    def fetch_parents(self, qids: Iterable[str]) -> dict[str, Any]:
        status, payload = self.request(parent_query(qids))
        if status != 200:
            raise RuntimeError("TEMPORAL_SOURCE_V2_PARENT_QUERY_FAILED")
        return payload


def initial_checkpoint(protocol_sha256: str = PROTOCOL_SHA256, *, timestamp: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "status": "INITIALIZED",
        "protocol_sha256": protocol_sha256,
        "backend": "QLever",
        "endpoint": QLEVER_ENDPOINT,
        "graph_scope": GRAPH_SCOPE,
        "main_view_rule_sha256": MAIN_VIEW_RULE_SHA256,
        "retrieval_timestamp": timestamp or utc_now(),
        "fresh_candidates_discovered": 0,
        "prior_identity_rejects": 0,
        "event_root_valid": 0,
        "time_valid": 0,
        "p580_used": 0,
        "p585_fallback_used": 0,
        "surface_leakage_pass": 0,
        "surface_leakage_reject": 0,
        "dedup_valid": 0,
        "diversity_valid": 0,
        "final_eligible_events": 0,
        "current_acquisition_offset": 0,
        "current_state": "NOT_STARTED",
        "class_counts": {},
        "artifact_chunk_count": 0,
        "last_verified_artifact": None,
        "canonical_events_count": 0,
        "families_count": 0,
        "v6_data_consumed": False,
        "v7_data_consumed": False,
        "v8_data_consumed": False,
    }


def write_checkpoint(path: Path, checkpoint: dict[str, Any]) -> None:
    atomic_write_json(path, checkpoint)


def load_checkpoint(path: Path, expected_protocol_sha256: str = PROTOCOL_SHA256) -> dict[str, Any]:
    checkpoint = json.loads(path.read_text(encoding="utf-8"))
    required = {"protocol_sha256": expected_protocol_sha256, "backend": "QLever", "graph_scope": GRAPH_SCOPE, "main_view_rule_sha256": MAIN_VIEW_RULE_SHA256}
    for key, expected in required.items():
        if checkpoint.get(key) != expected:
            raise RuntimeError(f"TEMPORAL_SOURCE_V2_CHECKPOINT_AUTHORITY_MISMATCH_{key}")
    if any(checkpoint.get(key) is not False for key in ("v6_data_consumed", "v7_data_consumed", "v8_data_consumed")):
        raise RuntimeError("TEMPORAL_SOURCE_V2_HISTORICAL_LINEAGE_CONSUMED")
    return checkpoint


def surface_is_safe(label: str) -> bool:
    normalized = " ".join(label.strip().split())
    return bool(normalized) and DATE_RE.search(normalized) is None


def _valid_time(value: dict[str, Any]) -> bool:
    return value.get("calendar") == GREGORIAN_QID and int(value.get("precision", -1)) >= MIN_PRECISION and bool(value.get("time_value"))


def resolve_canonical_time(candidate: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    for property_name, counter_name in (("P580", "p580"), ("P585", "p585")):
        values = [value for value in candidate.get("times", []) if value.get("property") == property_name and _valid_time(value)]
        identities = {(value["time_value"], int(value["precision"]), value["calendar"]) for value in values}
        if len(identities) > 1:
            return None, "AMBIGUOUS_CANONICAL_TIME"
        if len(identities) == 1:
            value = next(iter(values))
            return {**value, "canonical_property": property_name}, counter_name
    return None, "NO_VALID_CANONICAL_TIME"


def reachability(start: str, parents: dict[str, set[str]], memo: dict[str, set[str]], active: set[str] | None = None) -> set[str]:
    if start in memo:
        return set(memo[start])
    if active is None:
        active = set()
    if start in active:
        return set()
    if start in ROOTS:
        memo[start] = {start}
        return {start}
    active.add(start)
    found: set[str] = set()
    for parent in parents.get(start, set()):
        found.update(reachability(parent, parents, memo, active))
    active.remove(start)
    memo[start] = set(found)
    return found


def event_root_status(classes: Iterable[str], parents: dict[str, set[str]]) -> tuple[bool, str, str | None]:
    memo: dict[str, set[str]] = {}
    reachable: set[str] = set()
    for clazz in classes:
        reachable.update(reachability(clazz, parents, memo))
    if not reachable:
        return False, "NO_ROOT", None
    coarse = sorted(classes)[0] if classes else None
    return True, "BOTH_ROOTS" if len(reachable) == 2 else "ROOT_REACHABLE", coarse


def prepare_candidate(candidate: dict[str, Any], excluded_qids: set[str], parents: dict[str, set[str]]) -> tuple[dict[str, Any] | None, str]:
    qid = candidate.get("qid")
    if not isinstance(qid, str) or qid in excluded_qids:
        return None, "PRIOR_IDENTITY_REJECT"
    root_valid, root_status, coarse = event_root_status(candidate.get("direct_p31_qids", []), parents)
    if not root_valid:
        return None, "EVENT_ROOT_INVALID"
    canonical_time, time_source = resolve_canonical_time(candidate)
    if canonical_time is None:
        return None, time_source or "NO_VALID_CANONICAL_TIME"
    if not surface_is_safe(str(candidate.get("label", ""))):
        return None, "SURFACE_LEAKAGE_REJECT"
    identity = f"{qid}|{canonical_time['canonical_property']}|{canonical_time['time_value']}|precision={canonical_time['precision']}|calendar={canonical_time['calendar']}"
    event = {
        "qid": qid,
        "canonical_identity": identity,
        "label": candidate["label"],
        "canonical_time": canonical_time["time_value"],
        "canonical_property": canonical_time["canonical_property"],
        "coarse_class": coarse,
        "root_status": root_status,
        "time_source": time_source,
    }
    return event, "ELIGIBLE"


def select_events(events: Iterable[dict[str, Any]], *, target: int = TARGET_EVENTS, class_cap: int = CLASS_CAP) -> list[dict[str, Any]]:
    ordered = sorted(events, key=lambda event: sha256_bytes(f"PA_EXT_A_TEMPORAL_SOURCE_V2|{event['qid']}|{event['coarse_class']}".encode("utf-8")))
    selected: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    seen: set[str] = set()
    for event in ordered:
        if event["canonical_identity"] in seen:
            raise RuntimeError("TEMPORAL_SOURCE_V2_DUPLICATE_CANONICAL_IDENTITY")
        coarse = str(event["coarse_class"])
        if counts[coarse] >= class_cap:
            continue
        selected.append(event)
        seen.add(event["canonical_identity"])
        counts[coarse] += 1
        if len(selected) == target:
            break
    if len(selected) < target:
        raise RuntimeError("TEMPORAL_SOURCE_V2_INSUFFICIENT_DIVERSITY_VALID_EVENTS")
    return selected


def pair_events(events: Iterable[dict[str, Any]], *, target_families: int = TARGET_FAMILIES) -> list[dict[str, Any]]:
    ordered = sorted(events, key=lambda event: (event["canonical_time"], event["qid"], event["canonical_identity"]))
    used: set[str] = set()
    pairs: list[dict[str, Any]] = []
    for index, left in enumerate(ordered):
        if left["canonical_identity"] in used:
            continue
        for right in ordered[index + 1 :]:
            if right["canonical_identity"] in used or right["canonical_time"] == left["canonical_time"]:
                continue
            earlier, later = sorted((left, right), key=lambda event: (event["canonical_time"], event["qid"]))
            pair_index = len(pairs) + 1
            if pair_index % 2:
                first, second, direction = earlier, later, "EARLIER_TO_LATER"
            else:
                first, second, direction = later, earlier, "LATER_TO_EARLIER"
            pairs.append({"family_id": f"exta_temporal_v2_{pair_index:04d}", "pair_index": pair_index, "event_a": first, "event_b": second, "relation": "BEFORE", "direction": direction})
            used.update((left["canonical_identity"], right["canonical_identity"]))
            break
        if len(pairs) >= target_families:
            break
    if len(pairs) < target_families:
        raise RuntimeError("INSUFFICIENT_PAIRABLE_SOURCE")
    return pairs[:target_families]


def stopping_state(eligible_count: int, budget_exhausted: bool) -> str:
    if eligible_count >= RESERVE_EVENTS:
        return "STOP_AT_RESERVE_AND_SELECT"
    if budget_exhausted and eligible_count >= TARGET_EVENTS:
        return "READY_TO_PAIR"
    if budget_exhausted:
        return "INSUFFICIENT_FRESH_SOURCE"
    return "CONTINUE_ACQUISITION"


def publish_canonical(bundle: dict[str, Any], output_dir: Path = CANONICAL_DIR, *, synthetic: bool = False) -> None:
    if synthetic:
        raise RuntimeError("SYNTHETIC_CANONICAL_PUBLICATION_FORBIDDEN")
    if output_dir.exists():
        raise RuntimeError("TEMPORAL_SOURCE_V2_CANONICAL_OUTPUT_ALREADY_EXISTS")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=output_dir.parent))
    try:
        for name, value in bundle.items():
            atomic_write_json(temporary / name, value)
        os.replace(temporary, output_dir)
    finally:
        if temporary.exists():
            for child in temporary.iterdir():
                child.unlink()
            temporary.rmdir()


def _terminal_checkpoint(checkpoint: dict[str, Any], status: str, *, error: str | None = None) -> dict[str, Any]:
    """Return a terminal checkpoint update without weakening any guard."""
    updated = dict(checkpoint)
    updated["status"] = status
    updated["current_state"] = "TERMINAL"
    if error is not None:
        updated["last_verified_artifact"] = {"kind": "terminal_status", "status": status, "error": error}
    return updated


def _binding_value(binding: dict[str, Any], name: str) -> str | None:
    value = binding.get(name)
    if not isinstance(value, dict):
        return None
    raw = value.get("value")
    return raw if isinstance(raw, str) else None


def _bindings(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = payload.get("results", {})
    rows = results.get("bindings", []) if isinstance(results, dict) else []
    return [row for row in rows if isinstance(row, dict)]


def _qid(value: str | None) -> str | None:
    if not value:
        return None
    return value.rsplit("/", 1)[-1]


def _parse_event_page(payload: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in _bindings(payload):
        item = _qid(_binding_value(row, "item"))
        clazz = _qid(_binding_value(row, "class"))
        label = _binding_value(row, "label")
        if item is None or clazz is None:
            continue
        record = grouped.setdefault(item, {"qid": item, "direct_p31_qids": [], "label": label or ""})
        if clazz not in record["direct_p31_qids"]:
            record["direct_p31_qids"].append(clazz)
        if not record["label"] and label:
            record["label"] = label
    return [grouped[key] for key in sorted(grouped)]


def _parse_time_metadata(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    times: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in _bindings(payload):
        item = _qid(_binding_value(row, "item"))
        property_name = _binding_value(row, "property")
        date = _binding_value(row, "timeValue")
        precision = _binding_value(row, "precision")
        calendar = _qid(_binding_value(row, "calendar"))
        if item is None or property_name not in {"P580", "P585"} or date is None or precision is None or calendar is None:
            continue
        try:
            parsed_precision = int(precision)
        except ValueError:
            continue
        times[item].append({"property": property_name, "time_value": date, "precision": parsed_precision, "calendar": calendar})
    return times


def _parse_parent_metadata(payload: dict[str, Any]) -> dict[str, set[str]]:
    parents: dict[str, set[str]] = defaultdict(set)
    for row in _bindings(payload):
        clazz = _qid(_binding_value(row, "class"))
        parent = _qid(_binding_value(row, "parent"))
        if clazz and parent:
            parents[clazz].add(parent)
    return parents


def _load_freshness_exclusions() -> set[str]:
    """Load and hash-check the two frozen prior-identity sources."""
    manifest = EXP_DIR / "engineering" / "temp_feas_001" / "date_valid_pool_manifest.json"
    expected = "860351f16efa05c8991ee3fc76b7324b0d7a3c383a525e7f7f6c3d85e0f4d592"
    if not manifest.exists() or sha256_file(manifest) != expected:
        raise RuntimeError("TEMPORAL_SOURCE_V2_FRESHNESS_MANIFEST_UNAVAILABLE")
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    excluded = {str(row["wikidata_item_id"]) for row in payload.get("records", []) if row.get("wikidata_item_id")}
    raw_dir = EXP_DIR / "data" / "raw" / "wikidata_v8"
    page_paths = sorted(raw_dir.glob("candidate_page_*.json"))
    if not page_paths:
        raise RuntimeError("TEMPORAL_SOURCE_V2_V8_UNIVERSE_UNAVAILABLE")
    for page_path in page_paths:
        page = json.loads(page_path.read_text(encoding="utf-8"))
        for row in _bindings(page):
            item = _qid(_binding_value(row, "item"))
            if item:
                excluded.add(item)
    return excluded


def _parent_closure(client: QLeverClient, classes: Iterable[str]) -> dict[str, set[str]]:
    parents: dict[str, set[str]] = defaultdict(set)
    pending = set(classes)
    queried: set[str] = set()
    while pending:
        batch = sorted(pending - queried)
        if not batch:
            break
        queried.update(batch)
        response = client.fetch_parents(batch)
        discovered = _parse_parent_metadata(response)
        for clazz, values in discovered.items():
            parents[clazz].update(values)
        pending = {parent for values in discovered.values() for parent in values if parent not in queried and parent not in ROOTS}
    return parents


def _finish_source(
    checkpoint: dict[str, Any],
    eligible: list[dict[str, Any]],
    *,
    budget_exhausted: bool,
) -> dict[str, Any]:
    state = stopping_state(len(eligible), budget_exhausted)
    checkpoint["final_eligible_events"] = len(eligible)
    checkpoint["eligible_events"] = eligible
    checkpoint["current_state"] = state
    if state in {"STOP_AT_RESERVE_AND_SELECT", "READY_TO_PAIR"}:
        selected = select_events(eligible, target=TARGET_EVENTS, class_cap=CLASS_CAP)
        families = pair_events(selected, target_families=TARGET_FAMILIES)
        checkpoint["canonical_events_count"] = len(selected)
        checkpoint["families_count"] = len(families)
        publish_canonical({"eligible_events.json": eligible, "selected_events.json": selected, "families.json": families}, synthetic=False)
        checkpoint["status"] = "PUBLISHED"
        checkpoint["current_state"] = "TERMINAL"
        checkpoint["canonical_events_count"] = len(selected)
        return {"status": "PUBLISHED", "full_acquisition_performed": True, "families_count": len(families)}
    checkpoint["status"] = state
    if state == "INSUFFICIENT_FRESH_SOURCE":
        checkpoint["current_state"] = "TERMINAL"
    return {"status": state, "full_acquisition_performed": True, "eligible_count": len(eligible)}


def production_acquisition_core(client: QLeverClient, checkpoint: dict[str, Any]) -> dict[str, Any]:
    """Execute the frozen event-first acquisition funnel until a terminal state."""
    excluded = _load_freshness_exclusions()
    eligible = [dict(row) for row in checkpoint.get("eligible_events", [])]
    offset = int(checkpoint.get("current_acquisition_offset", 0))
    seen = {row.get("canonical_identity") for row in eligible}
    while True:
        payload = client.fetch_event_page(PAGE_SIZE, offset)
        candidates = _parse_event_page(payload)
        if not candidates:
            return _finish_source(checkpoint, eligible, budget_exhausted=True)
        qids = [candidate["qid"] for candidate in candidates]
        metadata = _parse_time_metadata(client.fetch_time_metadata(qids))
        classes = {clazz for candidate in candidates for clazz in candidate["direct_p31_qids"]}
        parents = _parent_closure(client, classes)
        page_events: list[dict[str, Any]] = []
        reasons = Counter()
        for candidate in candidates:
            candidate["times"] = metadata.get(candidate["qid"], [])
            prepared, reason = prepare_candidate(candidate, excluded, parents)
            reasons[reason] += 1
            if prepared is None or prepared["canonical_identity"] in seen:
                continue
            seen.add(prepared["canonical_identity"])
            page_events.append(prepared)
        chunk = {"offset": offset, "page": payload, "events": page_events, "reason_counts": dict(reasons), "retrieval_timestamp": utc_now()}
        atomic_write_json(RUNTIME_DIR / f"candidate_chunk_{offset:09d}.json", chunk)
        eligible.extend(page_events)
        checkpoint["fresh_candidates_discovered"] = int(checkpoint.get("fresh_candidates_discovered", 0)) + len(candidates)
        checkpoint["final_eligible_events"] = len(eligible)
        checkpoint["surface_leakage_pass"] = int(checkpoint.get("surface_leakage_pass", 0)) + reasons.get("ELIGIBLE", 0)
        checkpoint["surface_leakage_reject"] = int(checkpoint.get("surface_leakage_reject", 0)) + reasons.get("SURFACE_LEAKAGE_REJECT", 0)
        checkpoint["current_acquisition_offset"] = offset + PAGE_SIZE
        checkpoint["current_state"] = "RUNNING"
        checkpoint["status"] = "RUNNING"
        checkpoint["artifact_chunk_count"] = int(checkpoint.get("artifact_chunk_count", 0)) + 1
        checkpoint["eligible_events"] = eligible
        write_checkpoint(Path(str(checkpoint.get("_checkpoint_path", DEFAULT_CHECKPOINT_PATH))), checkpoint)
        offset += PAGE_SIZE
        if len(eligible) >= RESERVE_EVENTS:
            return _finish_source(checkpoint, eligible, budget_exhausted=False)


def run_production(
    *,
    client: QLeverClient | None = None,
    checkpoint_path: Path = DEFAULT_CHECKPOINT_PATH,
    production_core: Callable[[QLeverClient, dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run the guarded production entry point and return its terminal state.

    Protocol and checkpoint authority are checked before the backend gate.  A
    failed gate is persisted as a terminal fail-closed state.  The optional
    ``production_core`` argument is an offline qualification seam; ordinary
    CLI execution uses :func:`production_acquisition_core`.
    """
    load_protocol()
    if checkpoint_path.exists():
        checkpoint = load_checkpoint(checkpoint_path)
        checkpoint["current_state"] = "RESUMING"
    else:
        checkpoint = initial_checkpoint()
    checkpoint["_checkpoint_path"] = str(checkpoint_path)
    write_checkpoint(checkpoint_path, checkpoint)
    active_client = client or QLeverClient()
    try:
        gate = active_client.preflight()
    except Exception as exc:
        terminal = _terminal_checkpoint(checkpoint, "BACKEND_PREFLIGHT_FAILED", error=str(exc))
        write_checkpoint(checkpoint_path, terminal)
        return {"status": terminal["status"], "checkpoint": terminal, "error": str(exc)}
    checkpoint["status"] = "RUNNING"
    checkpoint["current_state"] = "RESUMING" if checkpoint.get("current_acquisition_offset", 0) else "STARTING"
    checkpoint["backend_preflight"] = gate
    write_checkpoint(checkpoint_path, checkpoint)
    core = production_core or globals()["production_acquisition_core"]
    try:
        result = core(active_client, checkpoint)
    except Exception as exc:
        terminal = _terminal_checkpoint(checkpoint, "PRODUCTION_CORE_FAILED", error=str(exc))
        write_checkpoint(checkpoint_path, terminal)
        return {"status": terminal["status"], "checkpoint": terminal, "error": str(exc)}
    checkpoint["status"] = result["status"]
    if result.get("status") in {"RUNNING", "CONTINUE_ACQUISITION"}:
        result = {**result, "status": "PRODUCTION_CORE_RETURNED_NONTERMINAL"}
    write_checkpoint(checkpoint_path, checkpoint)
    return {"status": result["status"], "checkpoint": checkpoint, "result": result}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--run", action="store_true", help="formal acquisition; never use this in engineering qualification")
    args = parser.parse_args(argv)
    load_protocol()
    if args.run:
        result = run_production()
        print(f"TEMPORAL_SOURCE_V2_RUN_STATUS={result['status']}")
        print(f"FULL_ACQUISITION_PERFORMED={str(result.get('result', {}).get('full_acquisition_performed', False)).lower()}")
        return 0 if result["status"] not in {"BACKEND_PREFLIGHT_FAILED", "PRODUCTION_CORE_FAILED"} else 1
    if args.preflight:
        print("TEMPORAL_SOURCE_V2_PROTOCOL_PREFLIGHT=PASS")
        print("FULL_ACQUISITION_PERFORMED=false")
        return 0
    parser.error("choose --preflight or --run")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
