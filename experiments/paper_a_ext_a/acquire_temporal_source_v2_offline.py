"""Final offline-hybrid TEMP-V2 source construction path.

The truthy dump is used only for bounded structural discovery.  Final time
eligibility is reconstructed from full entity responses and then passed to
the frozen TEMP-V2 scientific functions in ``acquire_temporal_source_v2``.
This module never downloads a dump by itself; the user supplies the path.
"""

from __future__ import annotations

import argparse
import bz2
import hashlib
import importlib.util
import json
import os
import re
import shutil
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator


EXP_DIR = Path(__file__).resolve().parent
PROTOCOL_PATH = EXP_DIR / "engineering" / "temp_feas_v2" / "temporal_source_v2_protocol.json"
DEFAULT_WORK_DIR = EXP_DIR / "data" / "temporal_source_v2_offline_runtime"
DEFAULT_SNAPSHOT_PATH = DEFAULT_WORK_DIR / "offline_structural_snapshot.json"
DEFAULT_HYDRATED_PATH = DEFAULT_WORK_DIR / "offline_hydrated_candidates.json"
DEFAULT_CHECKPOINT_PATH = DEFAULT_WORK_DIR / "offline_checkpoint.json"
DEFAULT_HYDRATION_CHECKPOINT_PATH = DEFAULT_WORK_DIR / "hydration_checkpoint.json"
PROTOCOL_SHA256 = "5018718739045b25514c8e94ede7e7ba6a99faa56b43c2156d27fbb97cfe2b6b"
ENTITY_API_ENDPOINT = "https://www.wikidata.org/w/api.php"
ENTITY_API_BATCH_SIZE = 50
ENTITY_API_MAX_RETRIES = 3
QID_RE = re.compile(r"^Q[1-9][0-9]*$")
ENTITY_URI_PREFIX = "http://www.wikidata.org/entity/"
WD_URI_PREFIX = "http://www.wikidata.org/prop/direct/"
RDFS_LABEL_URI = "http://www.w3.org/2000/01/rdf-schema#label"
P31_URI = WD_URI_PREFIX + "P31"
P279_URI = WD_URI_PREFIX + "P279"
ROOTS = ("Q1190554", "Q1656682")


def _load_frozen_runner():
    path = EXP_DIR / "acquire_temporal_source_v2.py"
    spec = importlib.util.spec_from_file_location("temp_v2_frozen_online_runner", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


RUNNER = _load_frozen_runner()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _qid(value: str | None) -> str | None:
    if not value:
        return None
    if value.startswith(ENTITY_URI_PREFIX):
        value = value[len(ENTITY_URI_PREFIX) :]
    return value if QID_RE.fullmatch(value) else None


def _unquote_literal(token: str) -> tuple[str, str | None]:
    if not token.startswith('"'):
        raise ValueError("not a literal")

    def decode_escape(index: int) -> tuple[str, int]:
        if index >= len(token):
            raise ValueError("incomplete N-Triples escape")
        escape = token[index]
        echar = {
            "t": "\t",
            "b": "\b",
            "n": "\n",
            "r": "\r",
            "f": "\f",
            '"': '"',
            "'": "'",
            "\\": "\\",
        }
        if escape in echar:
            return echar[escape], index + 1
        if escape not in {"u", "U"}:
            raise ValueError("invalid N-Triples escape")
        width = 4 if escape == "u" else 8
        end = index + 1 + width
        digits = token[index + 1 : end]
        if len(digits) != width or any(char not in "0123456789abcdefABCDEF" for char in digits):
            raise ValueError("invalid N-Triples UCHAR escape")
        codepoint = int(digits, 16)
        if codepoint > 0x10FFFF or 0xD800 <= codepoint <= 0xDFFF:
            raise ValueError("invalid Unicode scalar value")
        return chr(codepoint), end

    value: list[str] = []
    index = 1
    closing = None
    while index < len(token):
        char = token[index]
        if char == '"':
            closing = index
            break
        if char == "\\":
            decoded, index = decode_escape(index + 1)
            value.append(decoded)
            continue
        if char in {"\r", "\n"}:
            raise ValueError("raw line break in N-Triples literal")
        value.append(char)
        index += 1
    if closing is None:
        raise ValueError("unterminated literal")

    suffix = token[closing + 1 :]
    language = None
    if suffix.startswith("@"):
        language = suffix[1:]
        if not re.fullmatch(r"[A-Za-z]+(?:-[A-Za-z0-9]+)*", language):
            raise ValueError("invalid N-Triples language tag")
    elif suffix.startswith("^^"):
        # Preserve the existing parser contract: datatype is accepted but not
        # surfaced. Validate its IRIREF syntax instead of silently accepting a
        # malformed suffix.
        _decode_iri_ref(suffix[2:])
    elif suffix:
        raise ValueError("invalid N-Triples literal suffix")
    return "".join(value), language


def _decode_iri_ref(token: str) -> str:
    if not token.startswith("<") or not token.endswith(">"):
        raise ValueError("invalid IRIREF")
    body = token[1:-1]
    value: list[str] = []
    index = 0
    while index < len(body):
        char = body[index]
        if char == "\\":
            if index + 1 >= len(body) or body[index + 1] not in {"u", "U"}:
                raise ValueError("invalid IRIREF escape")
            escape = body[index + 1]
            width = 4 if escape == "u" else 8
            end = index + 2 + width
            digits = body[index + 2 : end]
            if len(digits) != width or any(item not in "0123456789abcdefABCDEF" for item in digits):
                raise ValueError("invalid IRIREF UCHAR escape")
            codepoint = int(digits, 16)
            if codepoint > 0x10FFFF or 0xD800 <= codepoint <= 0xDFFF:
                raise ValueError("invalid Unicode scalar value")
            value.append(chr(codepoint))
            index = end
            continue
        if ord(char) <= 0x20 or char in '<>"{}|^`':
            raise ValueError("invalid IRIREF character")
        value.append(char)
        index += 1
    return "".join(value)


def parse_nt_line(line: str) -> tuple[str, str, dict[str, str | None]] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if not stripped.endswith("."):
        raise ValueError("N-Triples line does not end with a period")
    body = stripped[:-1].rstrip()
    first = re.match(r"^(<[^>]+>)\s+(<[^>]+>)\s+(.+)$", body)
    if not first:
        raise ValueError("unsupported N-Triples structure")
    subject, predicate, object_token = first.groups()
    subject = _decode_iri_ref(subject)
    predicate = _decode_iri_ref(predicate)
    if object_token.startswith("<") and object_token.endswith(">"):
        obj = {"kind": "uri", "value": _decode_iri_ref(object_token), "language": None}
    elif object_token.startswith('"'):
        value, language = _unquote_literal(object_token)
        obj = {"kind": "literal", "value": value, "language": language}
    else:
        raise ValueError("unsupported N-Triples object")
    return subject, predicate, obj


class ProgressCounters:
    def __init__(self, compressed_file_size_bytes: int):
        self.compressed_file_size_bytes = compressed_file_size_bytes
        self.compressed_file_position_bytes: int | None = None
        self.triples_scanned = 0
        self.elapsed_seconds = 0.0

    def snapshot(self, started: float | None = None) -> dict[str, Any]:
        if started is not None and started > 0:
            self.elapsed_seconds = max(0.0, time.monotonic() - started)
        return {
            "compressed_file_size_bytes": self.compressed_file_size_bytes,
            "compressed_file_position_bytes": self.compressed_file_position_bytes,
            "triples_scanned": self.triples_scanned,
            "elapsed_seconds": self.elapsed_seconds,
        }


def iter_nt_triples(
    path: Path,
    counters: ProgressCounters | None = None,
    *,
    progress_callback: Callable[[ProgressCounters], None] | None = None,
    progress_interval_seconds: float = 60.0,
) -> Iterator[tuple[str, str, dict[str, str | None]]]:
    if not path.exists() or not path.is_file() or path.suffix.lower() != ".bz2":
        raise FileNotFoundError(f"expected readable .nt.bz2 dump: {path}")
    local = counters or ProgressCounters(path.stat().st_size)
    started = time.monotonic()
    next_report = started + max(0.1, progress_interval_seconds)
    with path.open("rb") as raw:
        with bz2.BZ2File(raw, "rb") as compressed:
            for raw_line in compressed:
                try:
                    line = raw_line.decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise RuntimeError("OFFLINE_TEMPORAL_DUMP_NOT_UTF8") from exc
                triple = parse_nt_line(line)
                if triple is None:
                    continue
                local.triples_scanned += 1
                local.elapsed_seconds = max(0.0, time.monotonic() - started)
                if progress_callback is not None and time.monotonic() >= next_report:
                    progress_callback(local)
                    next_report = time.monotonic() + max(0.1, progress_interval_seconds)
                yield triple
    local.elapsed_seconds = max(0.0, time.monotonic() - started)
    if progress_callback is not None:
        progress_callback(local)


def _checkpoint_base(dump_path: Path, work_dir: Path, expected_dump_sha256: str | None) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "status": "NOT_STARTED",
        "phase": "NOT_STARTED",
        "dump_path": str(dump_path),
        "dump_expected_sha256": expected_dump_sha256,
        "dump_actual_sha256": None,
        "dump_sha256_verified": False,
        "protocol_sha256": PROTOCOL_SHA256,
        "freshness_union_count": 6695,
        "snapshot_authority": None,
        "triples_scanned_per_pass": {},
        "structural_candidates_total": 0,
        "prior_identity_rejects": 0,
        "fresh_structural_candidates": 0,
        "labels_collected": 0,
        "hydrated": 0,
        "eligible": 0,
        "errors": [],
        "updated_at": utc_now(),
        "work_dir": str(work_dir),
    }


def _write_checkpoint(path: Path, value: dict[str, Any]) -> None:
    value = dict(value)
    value["updated_at"] = utc_now()
    atomic_write_json(path, value)


def _verify_protocol_and_freshness() -> set[str]:
    if sha256_file(PROTOCOL_PATH) != PROTOCOL_SHA256:
        raise RuntimeError("TEMPORAL_SOURCE_V2_PROTOCOL_SHA_MISMATCH")
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    if protocol.get("required_flags", {}).get("TEMPORAL_SOURCE_V2_DATA_ACCESSED") is not False:
        raise RuntimeError("TEMPORAL_SOURCE_V2_PROTOCOL_DATA_ALREADY_ACCESSED")
    info = RUNNER.load_freshness_exclusion_authority()
    if info["union_count"] != 6695:
        raise RuntimeError("TEMPORAL_SOURCE_V2_FRESHNESS_UNION_MISMATCH")
    return set(info["excluded_qids"])


def compute_root_compatible_classes(parents: dict[str, set[str]]) -> set[str]:
    nodes = set(parents)
    nodes.update(parent for values in parents.values() for parent in values)
    nodes.update(ROOTS)
    memo: dict[str, bool] = {}

    def reaches_root(node: str, active: set[str]) -> bool:
        if node in ROOTS:
            return True
        if node in memo:
            return memo[node]
        if node in active:
            return False
        active.add(node)
        result = any(reaches_root(parent, active) for parent in sorted(parents.get(node, set())))
        active.remove(node)
        memo[node] = result
        return result

    return {node for node in sorted(nodes) if reaches_root(node, set())}


def scan_p279_closure(
    dump_path: Path,
    *,
    progress_callback: Callable[[ProgressCounters], None] | None = None,
) -> tuple[dict[str, set[str]], set[str], ProgressCounters]:
    counters = ProgressCounters(dump_path.stat().st_size)
    parents: dict[str, set[str]] = defaultdict(set)
    for subject, predicate, obj in iter_nt_triples(dump_path, counters, progress_callback=progress_callback):
        if predicate != P279_URI or obj["kind"] != "uri":
            continue
        child = _qid(subject)
        parent = _qid(str(obj["value"]))
        if child and parent:
            parents[child].add(parent)
    return dict(parents), compute_root_compatible_classes(parents), counters


def scan_p31_candidates(
    dump_path: Path,
    compatible_classes: set[str],
    *,
    progress_callback: Callable[[ProgressCounters], None] | None = None,
) -> tuple[dict[str, set[str]], ProgressCounters]:
    counters = ProgressCounters(dump_path.stat().st_size)
    candidates: dict[str, set[str]] = defaultdict(set)
    for subject, predicate, obj in iter_nt_triples(dump_path, counters, progress_callback=progress_callback):
        if predicate != P31_URI or obj["kind"] != "uri":
            continue
        item = _qid(subject)
        clazz = _qid(str(obj["value"]))
        if item and clazz in compatible_classes:
            candidates[item].add(clazz)
    return dict(candidates), counters


def scan_labels(
    dump_path: Path,
    candidate_qids: set[str],
    *,
    progress_callback: Callable[[ProgressCounters], None] | None = None,
) -> tuple[dict[str, str], ProgressCounters]:
    counters = ProgressCounters(dump_path.stat().st_size)
    labels: dict[str, list[str]] = defaultdict(list)
    for subject, predicate, obj in iter_nt_triples(dump_path, counters, progress_callback=progress_callback):
        qid = _qid(subject)
        if predicate != RDFS_LABEL_URI or qid not in candidate_qids or obj["kind"] != "literal":
            continue
        if obj.get("language", "").lower() == "en":
            labels[qid].append(str(obj["value"]))
    if any(len(values) != 1 for values in labels.values()):
        raise RuntimeError("TEMPORAL_SOURCE_V2_OFFLINE_MULTIPLE_ENGLISH_LABELS")
    return {qid: values[0] for qid, values in labels.items()}, counters


def build_structural_snapshot(
    dump_path: Path,
    work_dir: Path,
    *,
    expected_dump_sha256: str | None = None,
    exclusions: set[str] | None = None,
    checkpoint_path: Path | None = None,
) -> dict[str, Any]:
    dump_path = dump_path.resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = checkpoint_path or work_dir / "offline_checkpoint.json"
    if checkpoint_path.exists():
        prior = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if prior.get("phase") not in {None, "NOT_STARTED"}:
            raise RuntimeError("TEMPORAL_SOURCE_V2_OFFLINE_CHECKPOINT_REQUIRES_EXPLICIT_RESUME")
    checkpoint = _checkpoint_base(dump_path, work_dir, expected_dump_sha256)
    checkpoint["phase"] = "PASS1_P279_RUNNING"
    checkpoint["status"] = "PASS1_P279_RUNNING"
    _write_checkpoint(checkpoint_path, checkpoint)
    excluded = set(exclusions) if exclusions is not None else _verify_protocol_and_freshness()
    if expected_dump_sha256 is not None:
        actual_dump_sha256 = sha256_file(dump_path)
        if actual_dump_sha256 != expected_dump_sha256:
            raise RuntimeError("TEMPORAL_SOURCE_V2_OFFLINE_DUMP_SHA_MISMATCH")
        checkpoint["dump_actual_sha256"] = actual_dump_sha256
        checkpoint["dump_sha256_verified"] = True
        _write_checkpoint(checkpoint_path, checkpoint)
    report = lambda counters: print(json.dumps({"Phase": checkpoint["phase"], **counters.snapshot()}, sort_keys=True))
    parents, compatible, pass1 = scan_p279_closure(dump_path, progress_callback=report)
    checkpoint["triples_scanned_per_pass"]["PASS1_P279"] = pass1.snapshot()
    checkpoint["phase"] = "PASS2_P31_RUNNING"
    checkpoint["status"] = "PASS2_P31_RUNNING"
    _write_checkpoint(checkpoint_path, checkpoint)
    candidates, pass2 = scan_p31_candidates(dump_path, compatible, progress_callback=report)
    checkpoint["triples_scanned_per_pass"]["PASS2_P31"] = pass2.snapshot()
    checkpoint["structural_candidates_total"] = len(candidates)
    checkpoint["prior_identity_rejects"] = sum(qid in excluded for qid in candidates)
    fresh = {qid: classes for qid, classes in candidates.items() if qid not in excluded}
    checkpoint["fresh_structural_candidates"] = len(fresh)
    checkpoint["phase"] = "PASS3_METADATA_RUNNING"
    checkpoint["status"] = "PASS3_METADATA_RUNNING"
    _write_checkpoint(checkpoint_path, checkpoint)
    labels, pass3 = scan_labels(dump_path, set(fresh), progress_callback=report)
    checkpoint["triples_scanned_per_pass"]["PASS3_METADATA"] = pass3.snapshot()
    checkpoint["labels_collected"] = len(labels)
    snapshot_candidates = [
        {"qid": qid, "direct_p31_qids": sorted(classes), "label": labels.get(qid)}
        for qid, classes in sorted(fresh.items())
    ]
    snapshot = {
        "schema_version": "1.0.0",
        "snapshot_type": "TEMPORAL_SOURCE_V2_OFFLINE_STRUCTURAL_SNAPSHOT",
        "dump_path": str(dump_path),
        "dump_expected_sha256": expected_dump_sha256,
        "protocol_sha256": PROTOCOL_SHA256,
        "freshness_union_count": len(excluded),
        "parents": {key: sorted(value) for key, value in sorted(parents.items())},
        "compatible_classes": sorted(compatible),
        "candidates": snapshot_candidates,
        "counts": {
            "structural_candidates_total": len(candidates),
            "prior_identity_rejects": sum(qid in excluded for qid in candidates),
            "fresh_structural_candidates": len(fresh),
            "labels_collected": len(labels),
        },
    }
    snapshot["snapshot_authority"] = sha256_bytes(canonical_json(snapshot))
    atomic_write_json(work_dir / "offline_structural_snapshot.json", snapshot)
    checkpoint["snapshot_authority"] = snapshot["snapshot_authority"]
    checkpoint["phase"] = "STRUCTURAL_SNAPSHOT_COMPLETE"
    checkpoint["status"] = "STRUCTURAL_SNAPSHOT_COMPLETE"
    _write_checkpoint(checkpoint_path, checkpoint)
    return snapshot


def _entity_label(entity: dict[str, Any]) -> str:
    labels = entity.get("labels", {})
    english = labels.get("en") if isinstance(labels, dict) else None
    if not isinstance(english, dict) or not isinstance(english.get("value"), str):
        raise RuntimeError("TEMPORAL_SOURCE_V2_OFFLINE_ENTITY_ENGLISH_LABEL_MISSING")
    return english["value"]


def _entity_times(entity: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    claims = entity.get("claims", {})
    if not isinstance(claims, dict):
        raise RuntimeError("TEMPORAL_SOURCE_V2_OFFLINE_ENTITY_CLAIMS_INVALID")
    for property_name in ("P580", "P585"):
        statements = claims.get(property_name, [])
        if not isinstance(statements, list):
            raise RuntimeError("TEMPORAL_SOURCE_V2_OFFLINE_ENTITY_STATEMENTS_INVALID")
        for statement in statements:
            mainsnak = statement.get("mainsnak", {}) if isinstance(statement, dict) else {}
            if mainsnak.get("snaktype") != "value":
                continue
            datavalue = mainsnak.get("datavalue", {}).get("value", {})
            if not isinstance(datavalue, dict):
                raise RuntimeError("TEMPORAL_SOURCE_V2_OFFLINE_ENTITY_TIME_INVALID")
            calendar = datavalue.get("calendarmodel") or datavalue.get("calendarModel")
            calendar_qid = _qid(str(calendar))
            if not isinstance(datavalue.get("time"), str) or calendar_qid is None:
                raise RuntimeError("TEMPORAL_SOURCE_V2_OFFLINE_ENTITY_TIME_INVALID")
            try:
                precision = int(datavalue["precision"])
            except (KeyError, TypeError, ValueError) as exc:
                raise RuntimeError("TEMPORAL_SOURCE_V2_OFFLINE_ENTITY_PRECISION_INVALID") from exc
            result.append({"property": property_name, "time_value": datavalue["time"], "precision": precision, "calendar": calendar_qid})
    return result


def entity_to_candidate(entity: dict[str, Any], structural: dict[str, Any]) -> dict[str, Any]:
    qid = _qid(str(entity.get("id")))
    if qid is None or qid != structural.get("qid"):
        raise RuntimeError("TEMPORAL_SOURCE_V2_OFFLINE_ENTITY_QID_MISMATCH")
    return {
        "qid": qid,
        "direct_p31_qids": list(structural.get("direct_p31_qids", [])),
        "label": _entity_label(entity),
        "times": _entity_times(entity),
    }


class WikidataEntityHydrationClient:
    """Bounded, cached, resumable full-entity hydration client."""

    def __init__(
        self,
        *,
        cache_dir: Path,
        request: Callable[[list[str]], dict[str, Any]] | None = None,
        endpoint: str = ENTITY_API_ENDPOINT,
        batch_size: int = ENTITY_API_BATCH_SIZE,
        max_retries: int = ENTITY_API_MAX_RETRIES,
        sleep: Callable[[float], None] = time.sleep,
        user_agent: str = "PA-EXT-A-TEMP-V2-offline-hybrid/1.0",
    ):
        if batch_size <= 0 or max_retries <= 0:
            raise ValueError("batch_size and max_retries must be positive")
        self.cache_dir = cache_dir
        self.request_override = request
        self.endpoint = endpoint
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.sleep = sleep
        self.user_agent = user_agent

    def _request_batch(self, qids: list[str]) -> dict[str, Any]:
        if self.request_override is not None:
            return self.request_override(list(qids))
        params = {
            "action": "wbgetentities",
            "ids": "|".join(qids),
            "format": "json",
            "props": "labels|claims",
            "languages": "en",
            "languagefallback": "0",
        }
        body = urllib.parse.urlencode(params).encode("utf-8")
        request = urllib.request.Request(self.endpoint, data=body, method="POST", headers={"User-Agent": self.user_agent, "Accept": "application/json"})
        last: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                    if not isinstance(payload, dict):
                        raise RuntimeError("malformed entity response")
                    return payload
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
                last = exc
                if attempt < self.max_retries:
                    self.sleep(float(2 ** (attempt - 1)))
        raise RuntimeError(f"TEMPORAL_SOURCE_V2_OFFLINE_ENTITY_REQUEST_FAILED:{last}")

    def hydrate(self, structural_candidates: list[dict[str, Any]], checkpoint_path: Path) -> list[dict[str, Any]]:
        ordered = sorted(structural_candidates, key=lambda row: row["qid"])
        qids = [row["qid"] for row in ordered]
        if any(not QID_RE.fullmatch(qid) for qid in qids):
            raise RuntimeError("TEMPORAL_SOURCE_V2_OFFLINE_INVALID_QID")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        checkpoint = {
            "status": "HYDRATING",
            "phase": "HYDRATING",
            "qids_sha256": sha256_bytes(canonical_json(qids)),
            "total_qids": len(qids),
            "hydrated_qids": [],
            "batch_size": self.batch_size,
            "endpoint": self.endpoint,
            "updated_at": utc_now(),
        }
        if checkpoint_path.exists():
            prior = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            if prior.get("qids_sha256") != checkpoint["qids_sha256"] or prior.get("endpoint") != self.endpoint:
                raise RuntimeError("TEMPORAL_SOURCE_V2_OFFLINE_HYDRATION_CHECKPOINT_MISMATCH")
            checkpoint.update(prior)
        hydrated_qids = set(checkpoint.get("hydrated_qids", []))
        for start in range(0, len(qids), self.batch_size):
            batch = []
            for qid in qids[start : start + self.batch_size]:
                if (self.cache_dir / f"{qid}.json").exists():
                    hydrated_qids.add(qid)
                else:
                    batch.append(qid)
            if batch:
                payload = self._request_batch(batch)
                entities = payload.get("entities")
                if not isinstance(entities, dict) or any(qid not in entities for qid in batch):
                    raise RuntimeError("TEMPORAL_SOURCE_V2_OFFLINE_ENTITY_RESPONSE_INCOMPLETE")
                for qid in batch:
                    entity = entities[qid]
                    if not isinstance(entity, dict):
                        raise RuntimeError("TEMPORAL_SOURCE_V2_OFFLINE_ENTITY_INVALID")
                    atomic_write_json(self.cache_dir / f"{qid}.json", entity)
                    hydrated_qids.add(qid)
            checkpoint["hydrated_qids"] = sorted(hydrated_qids)
            checkpoint["hydrated_count"] = len(hydrated_qids)
            checkpoint["updated_at"] = utc_now()
            _write_checkpoint(checkpoint_path, checkpoint)
        by_qid = {row["qid"]: row for row in ordered}
        result = []
        for qid in qids:
            entity = json.loads((self.cache_dir / f"{qid}.json").read_text(encoding="utf-8"))
            result.append(entity_to_candidate(entity, by_qid[qid]))
        checkpoint["status"] = "HYDRATION_COMPLETE"
        checkpoint["phase"] = "HYDRATION_COMPLETE"
        _write_checkpoint(checkpoint_path, checkpoint)
        return result


def finalize_hydrated_candidates(
    hydrated_candidates: Iterable[dict[str, Any]],
    parents: dict[str, set[str]],
    exclusions: set[str],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    eligible: list[dict[str, Any]] = []
    reasons: defaultdict[str, int] = defaultdict(int)
    for candidate in sorted(hydrated_candidates, key=lambda row: row["qid"]):
        event, reason = RUNNER.prepare_candidate(candidate, exclusions, parents)
        reasons[reason] += 1
        if event is not None:
            eligible.append(event)
    return eligible, dict(sorted(reasons.items()))


def preflight(dump_path: Path, *, expected_dump_sha256: str | None = None, work_dir: Path = DEFAULT_WORK_DIR) -> dict[str, Any]:
    if not dump_path.exists() or not dump_path.is_file() or dump_path.suffix.lower() != ".bz2":
        raise RuntimeError("TEMPORAL_SOURCE_V2_OFFLINE_DUMP_PATH_INVALID")
    with dump_path.open("rb"):
        pass
    exclusions = _verify_protocol_and_freshness()
    canonical = EXP_DIR / "data" / "wikidata_temporal_source_v2"
    if canonical.exists():
        raise RuntimeError("TEMPORAL_SOURCE_V2_CANONICAL_OUTPUT_ALREADY_EXISTS")
    usage = shutil.disk_usage(work_dir.anchor or str(work_dir.parent))
    return {
        "valid": True,
        "dump_path": str(dump_path.resolve()),
        "compressed_file_size_bytes": dump_path.stat().st_size,
        "expected_dump_sha256": expected_dump_sha256,
        "freshness_union_count": len(exclusions),
        "free_bytes_at_preflight": usage.free,
        "protocol_sha256": PROTOCOL_SHA256,
        "canonical_output_exists": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dump", type=Path)
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    parser.add_argument("--expected-dump-sha256")
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--scan", action="store_true")
    parser.add_argument("--hydrate", action="store_true")
    parser.add_argument("--finalize", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args(argv)
    if not args.dump:
        parser.error("--dump is required")
    if args.preflight:
        print(json.dumps(preflight(args.dump, expected_dump_sha256=args.expected_dump_sha256, work_dir=args.work_dir), sort_keys=True))
        return 0
    if args.scan or args.run:
        snapshot = build_structural_snapshot(args.dump, args.work_dir, expected_dump_sha256=args.expected_dump_sha256)
        atomic_write_json(args.work_dir / "offline_structural_snapshot.json", snapshot)
        print(f"TEMPORAL_SOURCE_V2_OFFLINE_SCAN_STATUS=STRUCTURAL_SNAPSHOT_COMPLETE")
    if args.hydrate or args.run:
        snapshot = json.loads((args.work_dir / "offline_structural_snapshot.json").read_text(encoding="utf-8"))
        client = WikidataEntityHydrationClient(cache_dir=args.work_dir / "entity_cache")
        candidates = client.hydrate(snapshot["candidates"], args.work_dir / "hydration_checkpoint.json")
        atomic_write_json(args.work_dir / "offline_hydrated_candidates.json", candidates)
        print("TEMPORAL_SOURCE_V2_OFFLINE_HYDRATION_STATUS=HYDRATION_COMPLETE")
    if args.finalize or args.run:
        snapshot = json.loads((args.work_dir / "offline_structural_snapshot.json").read_text(encoding="utf-8"))
        hydrated = json.loads((args.work_dir / "offline_hydrated_candidates.json").read_text(encoding="utf-8"))
        exclusions = _verify_protocol_and_freshness()
        parents = {key: set(value) for key, value in snapshot["parents"].items()}
        eligible, reasons = finalize_hydrated_candidates(hydrated, parents, exclusions)
        print(json.dumps({"eligible": len(eligible), "reasons": reasons}, sort_keys=True))
        if len(eligible) < RUNNER.TARGET_EVENTS:
            print("TEMPORAL_SOURCE_V2_OFFLINE_FINALIZE_STATUS=INSUFFICIENT_FRESH_SOURCE")
            return 1
        selected = RUNNER.select_events(eligible)
        families = RUNNER.pair_events(selected)
        if len(families) != RUNNER.TARGET_FAMILIES:
            raise RuntimeError("TEMPORAL_SOURCE_V2_OFFLINE_PAIR_COUNT_UNEXPECTED")
        print("TEMPORAL_SOURCE_V2_OFFLINE_FINALIZE_STATUS=READY_TO_PUBLISH")
    if not any((args.preflight, args.scan, args.hydrate, args.finalize, args.run)):
        parser.error("choose --preflight, --scan, --hydrate, --finalize, or --run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
