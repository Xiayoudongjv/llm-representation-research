"""Bounded QLever main-view qualification for PA-EXT-A temporal V6.

This is an engineering diagnostic only.  It uses fixed QIDs and one
predefined calendar-year window; it never performs temporal acquisition or
creates scientific assets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
REPORT_PATH = Path(__file__).with_name("qlever_main_view_qualification_r2.json")
LEGACY_ENDPOINT = "https://query.wikidata.org/sparql"
QLEVER_ENDPOINT = "https://qlever.dev/api/wikidata"
OCCURRENCE_QID = "Q1190554"
GREGORIAN_QID = "Q1985727"
MINIMUM_PRECISION = 11
FIXED_QIDS = [
    "Q55867177", "Q108147144", "Q115570791", "Q135686876",
    "Q116756558", "Q126366802", "Q108810473", "Q137841012",
    "Q135656007", "Q130382184", "Q123292342", "Q63208625",
    "Q6615146", "Q1501240", "Q127147513", "Q78140346",
    "Q123367418", "Q84078485", "Q63253107", "Q134311152",
]

# Published WDQS scholarly split rule: direct, non-deprecated P31 only.
# P279 subclass ancestry is deliberately not used for the split decision.
SCHOLARLY_P31_QIDS = [
    "Q13442814", "Q7318358", "Q2782326", "Q815382", "Q1348305",
    "Q187685", "Q1907875", "Q18918145", "Q1266946", "Q23927052",
    "Q1504425", "Q45182324", "Q1402850", "Q7316896", "Q580922",
    "Q30749496", "Q111475835", "Q92998777", "Q114613919", "Q798134",
    "Q10885494", "Q51282918", "Q51282711", "Q111475860", "Q51283092",
    "Q15706459", "Q59387148", "Q110716513", "Q58897583", "Q51283145",
    "Q54670950", "Q91901000", "Q51283219", "Q70471362",
]


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def qid(value: str | None) -> str | None:
    if not value:
        return None
    return value.rsplit("/", 1)[-1] if "/entity/" in value else value


def binding_value(binding: dict[str, Any], key: str) -> str | None:
    value = binding.get(key, {}).get("value")
    return value if isinstance(value, str) else None


def values_clause(items: list[str]) -> str:
    return " ".join(f"wd:{item}" for item in items)


def main_view_filter() -> str:
    scholarly = values_clause(SCHOLARLY_P31_QIDS)
    return f"""FILTER NOT EXISTS {{
    ?item p:P13046 ?publicationStatement .
    ?publicationStatement wikibase:rank ?publicationRank .
    FILTER(?publicationRank != wikibase:DeprecatedRank)
  }}
  FILTER NOT EXISTS {{
    ?item p:P31 ?scholarlyInstanceStatement .
    ?scholarlyInstanceStatement ps:P31 ?scholarlyInstance ;
      wikibase:rank ?scholarlyInstanceRank .
    FILTER(?scholarlyInstanceRank != wikibase:DeprecatedRank)
    VALUES ?scholarlyInstance {{ {scholarly} }}
  }}"""


def fixed_query(filtered: bool) -> str:
    values = values_clause(FIXED_QIDS)
    filter_text = main_view_filter() if filtered else ""
    return f"""PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX ps: <http://www.wikidata.org/prop/statement/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX wikibase: <http://wikiba.se/ontology#>
SELECT DISTINCT ?item ?label ?date ?precision ?calendar ?dateRank
  ?instance ?instanceRank ?parent ?publicationType WHERE {{
  VALUES ?item {{ {values} }}
  {filter_text}
  OPTIONAL {{ ?item rdfs:label ?label . FILTER(lang(?label) = "en") }}
  OPTIONAL {{
    ?item p:P585 ?dateStatement .
    ?dateStatement ps:P585 ?date ; wikibase:rank ?dateRank .
    OPTIONAL {{ ?dateStatement wikibase:timePrecision ?precision }}
    OPTIONAL {{ ?dateStatement wikibase:timeCalendarModel ?calendar }}
  }}
  OPTIONAL {{
    ?item p:P31 ?instanceStatement .
    ?instanceStatement ps:P31 ?instance ;
      wikibase:rank ?instanceRank .
    OPTIONAL {{ ?instance wdt:P279 ?parent }}
  }}
  OPTIONAL {{ ?item wdt:P13046 ?publicationType }}
}} ORDER BY ?item ?date ?instance ?parent"""


def window_query(filtered: bool) -> str:
    filter_text = main_view_filter() if filtered else ""
    return f"""PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX ps: <http://www.wikidata.org/prop/statement/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?item ?date ?precision ?calendar ?publicationType ?instance WHERE {{
  ?item p:P585 ?dateStatement .
  ?dateStatement ps:P585 ?date ; wikibase:rank ?dateRank .
  {filter_text}
  OPTIONAL {{ ?dateStatement wikibase:timePrecision ?precision }}
  OPTIONAL {{ ?dateStatement wikibase:timeCalendarModel ?calendar }}
  OPTIONAL {{ ?item wdt:P13046 ?publicationType }}
  OPTIONAL {{ ?item wdt:P31 ?instance }}
  FILTER(?date >= "1900-01-01T00:00:00Z"^^xsd:dateTime
    && ?date < "1901-01-01T00:00:00Z"^^xsd:dateTime)
}} ORDER BY ASC(?date) ASC(?item) LIMIT 20"""


def run_query(endpoint: str, query: str) -> dict[str, Any]:
    body = urllib.parse.urlencode({"query": query}).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Accept": "application/sparql-results+json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "PA-EXT-A-005R2-QEQ-R2/1.0 (bounded read-only diagnostic)",
        },
    )
    retrieved_at = datetime.now(timezone.utc).isoformat()
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = response.read()
            status = response.status
            content_type = response.headers.get("Content-Type", "")
        parsed = json.loads(payload)
        return {
            "http_status": status,
            "content_type": content_type,
            "query_sha256": sha256_text(query),
            "row_count": len(parsed.get("results", {}).get("bindings", [])),
            "bindings": parsed.get("results", {}).get("bindings", []),
            "retrieved_at": retrieved_at,
        }
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        body_text = ""
        if isinstance(exc, urllib.error.HTTPError):
            try:
                body_text = exc.read().decode("utf-8", errors="replace")[:1000]
            except Exception:
                body_text = "<unreadable error body>"
        return {
            "http_status": getattr(exc, "code", None),
            "query_sha256": sha256_text(query),
            "error": f"{type(exc).__name__}: {exc}",
            "error_body_prefix": body_text,
            "retrieved_at": retrieved_at,
        }


def fixed_records(bindings: list[dict[str, Any]]) -> dict[str, dict[str, set[Any]]]:
    fields = ("labels", "dates", "metadata", "date_ranks", "p31", "p31_ranks", "p279", "pub")
    result = {item: {field: set() for field in fields} for item in FIXED_QIDS}
    for binding in bindings:
        item = qid(binding_value(binding, "item"))
        if item not in result:
            continue
        label = binding_value(binding, "label")
        date = binding_value(binding, "date")
        precision = binding_value(binding, "precision")
        calendar = qid(binding_value(binding, "calendar"))
        if label:
            result[item]["labels"].add(label)
        if date:
            result[item]["dates"].add(date)
            if binding_value(binding, "dateRank"):
                result[item]["date_ranks"].add(binding_value(binding, "dateRank"))
            if precision or calendar:
                result[item]["metadata"].add((date, precision, calendar))
        instance = qid(binding_value(binding, "instance"))
        if instance:
            result[item]["p31"].add(instance)
            if binding_value(binding, "instanceRank"):
                result[item]["p31_ranks"].add((instance, binding_value(binding, "instanceRank")))
        parent = qid(binding_value(binding, "parent"))
        if parent:
            result[item]["p279"].add(parent)
        publication = qid(binding_value(binding, "publicationType"))
        if publication:
            result[item]["pub"].add(publication)
    return result


def freeze_record_eligible(record: dict[str, set[Any]]) -> bool:
    if len(record["labels"]) != 1 or len(record["metadata"]) != 1:
        return False
    date, precision, calendar = next(iter(record["metadata"]))
    del date
    try:
        if int(precision or "0") < MINIMUM_PRECISION:
            return False
    except ValueError:
        return False
    if calendar != GREGORIAN_QID:
        return False
    return OCCURRENCE_QID in record["p31"] or OCCURRENCE_QID in record["p279"]


def compare_fixed(left: dict[str, dict[str, set[Any]]], right: dict[str, dict[str, set[Any]]]) -> dict[str, Any]:
    mismatches = []
    for item in FIXED_QIDS:
        for field in ("labels", "dates", "metadata", "date_ranks", "p31", "p279", "pub"):
            if left[item][field] != right[item][field]:
                mismatches.append({
                    "item": item,
                    "field": field,
                    "left": sorted(map(str, left[item][field])),
                    "right": sorted(map(str, right[item][field])),
                })
    return {"mismatch_count": len(mismatches), "mismatches": mismatches[:100]}


def compact_window(bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for binding in bindings:
        item = qid(binding_value(binding, "item"))
        instances = qid(binding_value(binding, "instance"))
        publication = qid(binding_value(binding, "publicationType"))
        rows.append({
            "item": item,
            "date": binding_value(binding, "date"),
            "precision": binding_value(binding, "precision"),
            "calendar": qid(binding_value(binding, "calendar")),
            "publication_type": publication,
            "direct_p31": instances,
            "scholarly_only_marker": publication is not None or instances in SCHOLARLY_P31_QIDS,
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", help="run bounded external probes")
    args = parser.parse_args()
    if not args.run:
        parser.error("This diagnostic is explicit: pass --run")

    legacy_fixed = run_query(LEGACY_ENDPOINT, fixed_query(False))
    qlever_fixed_raw = run_query(QLEVER_ENDPOINT, fixed_query(False))
    qlever_fixed_main = run_query(QLEVER_ENDPOINT, fixed_query(True))
    legacy_window = run_query(LEGACY_ENDPOINT, window_query(False))
    qlever_window_raw = run_query(QLEVER_ENDPOINT, window_query(False))
    qlever_window_main = run_query(QLEVER_ENDPOINT, window_query(True))

    report: dict[str, Any] = {
        "qualification_id": "PA-EXT-A-005R2-QEQ-R2",
        "diagnostic_only": True,
        "v6_modified": False,
        "formal_acquisition": False,
        "temporal_pairs_created": False,
        "model_inference": False,
        "raw_graph_scope": "UNIFIED",
        "fixed_qids": FIXED_QIDS,
        "fixed_window": {"start": "1900-01-01", "end_exclusive": "1901-01-01", "limit": 20},
        "scholarly_exclusion_rule": {
            "non_deprecated_p13046": True,
            "non_deprecated_direct_p31_in_published_list": True,
            "p279_ancestry_used_for_graph_split": False,
            "scholarly_p31_qids": SCHOLARLY_P31_QIDS,
        },
        "queries": {
            "legacy_fixed": {k: v for k, v in legacy_fixed.items() if k != "bindings"},
            "qlever_fixed_raw": {k: v for k, v in qlever_fixed_raw.items() if k != "bindings"},
            "qlever_fixed_main_view": {k: v for k, v in qlever_fixed_main.items() if k != "bindings"},
            "legacy_window": {k: v for k, v in legacy_window.items() if k != "bindings"},
            "qlever_window_raw": {k: v for k, v in qlever_window_raw.items() if k != "bindings"},
            "qlever_window_main_view": {k: v for k, v in qlever_window_main.items() if k != "bindings"},
        },
    }

    if all(result.get("http_status") == 200 for result in (legacy_fixed, qlever_fixed_raw, qlever_fixed_main)):
        legacy_records = fixed_records(legacy_fixed["bindings"])
        raw_records = fixed_records(qlever_fixed_raw["bindings"])
        main_records = fixed_records(qlever_fixed_main["bindings"])
        report["fixed_comparison"] = {
            "legacy_vs_qlever_main_view": compare_fixed(legacy_records, main_records),
            "qlever_raw_vs_qlever_main_view": compare_fixed(raw_records, main_records),
            "legacy_eligible_qids": [item for item in FIXED_QIDS if freeze_record_eligible(legacy_records[item])],
            "qlever_main_view_eligible_qids": [item for item in FIXED_QIDS if freeze_record_eligible(main_records[item])],
            "qlever_raw_eligible_qids": [item for item in FIXED_QIDS if freeze_record_eligible(raw_records[item])],
            "qlever_raw_items_with_p585": [item for item in FIXED_QIDS if raw_records[item]["dates"]],
            "qlever_main_view_items_with_p585": [item for item in FIXED_QIDS if main_records[item]["dates"]],
        }
    else:
        report["fixed_comparison"] = {"status": "NOT_EXECUTABLE_DUE_TO_ENDPOINT_FAILURE"}

    if qlever_window_raw.get("http_status") == 200 and qlever_window_main.get("http_status") == 200:
        raw_window = compact_window(qlever_window_raw["bindings"])
        main_window = compact_window(qlever_window_main["bindings"])
        raw_items = [row["item"] for row in raw_window]
        main_items = [row["item"] for row in main_window]
        removed = [item for item in raw_items if item not in main_items]
        report["global_order_diagnostic"] = {
            "raw_window": raw_window,
            "main_view_window": main_window,
            "raw_items_removed_by_main_view_filter": removed,
            "scholarly_only_raw_items_in_window": [row["item"] for row in raw_window if row["scholarly_only_marker"]],
            "order_changed": raw_items != main_items,
            "risk_observed_in_fixed_window": bool(removed),
        }
    else:
        report["global_order_diagnostic"] = {"status": "NOT_EXECUTABLE_DUE_TO_ENDPOINT_FAILURE"}

    report["qlever_query_compatibility"] = (
        "PASS" if qlever_fixed_raw.get("http_status") == 200 and qlever_fixed_main.get("http_status") == 200 else "FAIL"
    )
    report["main_view_filter_implemented"] = (
        qlever_fixed_main.get("http_status") == 200
        and qlever_window_main.get("http_status") == 200
    )
    fixed = report.get("fixed_comparison", {})
    fixed_cmp = fixed.get("legacy_vs_qlever_main_view", {})
    report["field_concordance"] = "PASS" if fixed_cmp.get("mismatch_count") == 0 else "PARTIAL"
    report["eligibility_concordance"] = (
        "PASS"
        if fixed.get("legacy_eligible_qids") == fixed.get("qlever_main_view_eligible_qids")
        else "PARTIAL"
    )
    observed_risk = report.get("global_order_diagnostic", {}).get("risk_observed_in_fixed_window")
    report["global_order_risk"] = "PRESENT" if observed_risk else "NOT_ESTABLISHED"
    report["main_view_candidate_equivalence"] = (
        "ESTABLISHED"
        if report["field_concordance"] == "PASS"
        and report["eligibility_concordance"] == "PASS"
        and report["global_order_risk"] == "ABSENT"
        else "NOT_ESTABLISHED"
    )
    report["recommendation"] = "RECOMMEND_KEEP_V6"
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "report_path": str(REPORT_PATH),
        "qlever_query_compatibility": report["qlever_query_compatibility"],
        "main_view_filter_implemented": report["main_view_filter_implemented"],
        "main_view_candidate_equivalence": report["main_view_candidate_equivalence"],
        "field_concordance": report["field_concordance"],
        "eligibility_concordance": report["eligibility_concordance"],
        "global_order_risk": report["global_order_risk"],
        "recommendation": report["recommendation"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
