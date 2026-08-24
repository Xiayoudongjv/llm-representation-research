"""Bounded, noncanonical network qualification for the PA-EXT-A V8 query."""

from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from qlever_v8_literal_main_view import QLEVER_ENDPOINT, candidate_query


EXP_DIR = Path(__file__).resolve().parent
ENGINEERING_DIR = EXP_DIR / "engineering"
REPORT_PATH = ENGINEERING_DIR / "qlever_v8_literal_binding_qualification.json"
FIXED_METADATA_PROBE_QIDS = (
    "Q55867177", "Q108147144", "Q115570791", "Q135686876", "Q116756558",
    "Q126366802", "Q108810473", "Q137841012", "Q135656007", "Q130382184",
    "Q123292342", "Q63208625", "Q6615146", "Q1501240", "Q127147513",
    "Q78140346", "Q123367418", "Q84078485", "Q63253107", "Q134311152",
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def query_sha256(query: str) -> str:
    return sha256_bytes(query.encode("utf-8"))


def _request(query: str) -> tuple[bytes, int]:
    body = urllib.parse.urlencode({"query": query}).encode("utf-8")
    request = urllib.request.Request(
        QLEVER_ENDPOINT,
        data=body,
        method="POST",
        headers={
            "Accept": "application/sparql-results+json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "PA-EXT-A-005R2-V8 bounded qualification/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read(), int(response.status)


def _bindings(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return list(payload.get("results", {}).get("bindings", []))


def _value(binding: dict[str, Any], key: str) -> str | None:
    value = binding.get(key, {}).get("value")
    return value if isinstance(value, str) else None


def _qid(value: str | None) -> str | None:
    if value is None:
        return None
    suffix = value.rsplit("/", 1)[-1]
    return suffix if suffix.startswith("Q") and suffix[1:].isdigit() else None


def _metadata_query(qids: list[str]) -> str:
    values = " ".join(f"wd:{qid}" for qid in sorted(set(qids)))
    return f"""PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX ps: <http://www.wikidata.org/prop/statement/>
PREFIX psv: <http://www.wikidata.org/prop/statement/value/>
PREFIX wikibase: <http://wikiba.se/ontology#>
SELECT ?item ?label ?date ?timeValue ?precision ?calendar WHERE {{
  VALUES ?item {{ {values} }}
  ?item rdfs:label ?label .
  FILTER(lang(?label)="en")
  ?item p:P585 ?stmt .
  ?stmt ps:P585 ?date .
  ?stmt psv:P585 ?valueNode .
  ?valueNode wikibase:timeValue ?timeValue ;
             wikibase:timePrecision ?precision ;
             wikibase:timeCalendarModel ?calendar .
}}"""


def _p31_query(qids: list[str]) -> str:
    values = " ".join(f"wd:{qid}" for qid in sorted(set(qids)))
    return f"""PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
SELECT ?item ?class WHERE {{
  VALUES ?item {{ {values} }}
  ?item wdt:P31 ?class .
}}"""


def _p279_query(classes: list[str]) -> str:
    values = " ".join(f"wd:{qid}" for qid in sorted(set(classes)))
    return f"""PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
SELECT ?class ?parent WHERE {{
  VALUES ?class {{ {values} }}
  ?class wdt:P279 ?parent .
}}"""


def _run(query: str) -> dict[str, Any]:
    payload, status = _request(query)
    parsed = json.loads(payload.decode("utf-8"))
    return {
        "query_sha256": query_sha256(query),
        "payload_sha256": sha256_bytes(payload),
        "payload_bytes": len(payload),
        "http_status": status,
        "binding_count": len(_bindings(parsed)),
        "payload": parsed,
    }


def qualify() -> dict[str, Any]:
    candidate = _run(candidate_query(limit=100, offset=0))
    candidate_bindings = _bindings(candidate.pop("payload"))
    literal_count = sum(1 for row in candidate_bindings if row.get("date", {}).get("type") == "literal")
    candidate_qids = {_qid(_value(row, "item")) for row in candidate_bindings if _qid(_value(row, "item"))}
    qids = sorted(candidate_qids | set(FIXED_METADATA_PROBE_QIDS))
    metadata = _run(_metadata_query(qids)) if qids else None
    metadata_bindings = _bindings(metadata.pop("payload")) if metadata else []
    metadata_diagnostics = {
        "date_literal_count": sum(1 for row in metadata_bindings if row.get("date", {}).get("type") == "literal"),
        "time_value_literal_count": sum(1 for row in metadata_bindings if row.get("timeValue", {}).get("type") == "literal"),
        "precision_literal_count": sum(1 for row in metadata_bindings if row.get("precision", {}).get("type") == "literal"),
        "calendar_qids": sorted({_qid(_value(row, "calendar")) for row in metadata_bindings}),
        "precision_values": sorted({_value(row, "precision") for row in metadata_bindings}),
    }
    positive_metadata = [
        row for row in metadata_bindings
        if row.get("date", {}).get("type") == "literal"
        and row.get("timeValue", {}).get("type") == "literal"
        and row.get("precision", {}).get("type") == "literal"
        and _qid(_value(row, "calendar")) == "Q1985727"
        and int(_value(row, "precision") or "0") >= 11
    ]
    p31 = _run(_p31_query(qids)) if qids else None
    classes = sorted({_qid(_value(row, "class")) for row in _bindings(p31["payload"]) if _qid(_value(row, "class"))}) if p31 else []
    p31_payload = p31.pop("payload") if p31 else {"results": {"bindings": []}}
    p279 = _run(_p279_query(classes[:20])) if classes else None
    p279_payload = p279.pop("payload") if p279 else {"results": {"bindings": []}}
    report = {
        "schema_version": "1.0.0",
        "status": "PASS" if (
            candidate["http_status"] == 200
            and candidate["binding_count"] == 100
            and literal_count == candidate["binding_count"]
            and bool(positive_metadata)
            and bool(p31 and p31["http_status"] == 200)
            and bool(p279 and p279["http_status"] == 200)
        ) else "FAIL",
        "qualification_scope": "BOUNDED_NONCANONICAL_V8_SCHEMA_QUALIFICATION",
        "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
        "backend": "QLever",
        "endpoint": QLEVER_ENDPOINT,
        "raw_graph_scope": "UNIFIED",
        "candidate_query_sha256": candidate["query_sha256"],
        "candidate_query_limit": 100,
        "candidate_query_offset": 0,
        "candidate_http_status": candidate["http_status"],
        "candidate_binding_count": candidate["binding_count"],
        "candidate_literal_date_count": literal_count,
        "candidate_literal_binding_rate": f"{literal_count}/{candidate['binding_count']}",
        "fixed_metadata_probe_qid_count": len(FIXED_METADATA_PROBE_QIDS),
        "candidate_page_qid_count_in_metadata_probe": len(candidate_qids),
        "metadata_query_sha256": metadata["query_sha256"] if metadata else None,
        "metadata_binding_count": len(metadata_bindings),
        "metadata_diagnostics": metadata_diagnostics,
        "positive_time_metadata_count": len(positive_metadata),
        "positive_time_metadata_path": bool(positive_metadata),
        "p31_query_sha256": p31["query_sha256"] if p31 else None,
        "p31_http_status": p31["http_status"] if p31 else None,
        "p31_binding_count": len(_bindings(p31_payload)),
        "p31_retrieval": bool(p31 and p31["http_status"] == 200),
        "p279_query_sha256": p279["query_sha256"] if p279 else None,
        "p279_http_status": p279["http_status"] if p279 else None,
        "p279_binding_count": len(_bindings(p279_payload)),
        "p279_retrieval": bool(p279 and p279["http_status"] == 200),
        "main_view_filter": True,
        "v7_raw_lineage_consumed": False,
        "temporal_families_created": 0,
        "formal_v8_acquisition_performed": False,
        "model_inference_performed": False,
    }
    ENGINEERING_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    report = qualify()
    print(f"PA_EXT_A_V8_LITERAL_BINDING_QUALIFICATION = {report['status']}")
    print(f"LITERAL_BINDING_RATE = {report['candidate_literal_binding_rate']}")
    print(f"POSITIVE_TIME_METADATA_PATH = {str(report['positive_time_metadata_path']).lower()}")
    print(f"P31_RETRIEVAL = {str(report['p31_retrieval']).lower()}")
    print(f"P279_RETRIEVAL = {str(report['p279_retrieval']).lower()}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
