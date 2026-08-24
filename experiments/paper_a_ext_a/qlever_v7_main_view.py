"""Offline query construction for the prospective PA-EXT-A V7 route.

This module does not access the network, load data, or create outputs.  It
only constructs the frozen QLever main-view candidate query.  The scholarly
rule is bound by the separate ``v7_main_view_rule.json`` authority.
"""

from __future__ import annotations

from pathlib import Path


EXP_DIR = Path(__file__).resolve().parent
QLEVER_ENDPOINT = "https://qlever.dev/api/wikidata"
RAW_GRAPH_SCOPE = "UNIFIED"
V7_FORMAL_START_OFFSET = 0
HISTORICAL_V6_CHECKPOINT_OFFSET = 100
RULE_PATH = EXP_DIR / "v7_main_view_rule.json"

SCHOLARLY_P31_QIDS = (
    "Q13442814", "Q7318358", "Q2782326", "Q815382", "Q1348305",
    "Q187685", "Q1907875", "Q18918145", "Q1266946", "Q23927052",
    "Q1504425", "Q45182324", "Q1402850", "Q7316896", "Q580922",
    "Q30749496", "Q111475835", "Q92998777", "Q114613919", "Q798134",
    "Q10885494", "Q51282918", "Q51282711", "Q111475860", "Q51283092",
    "Q15706459", "Q59387148", "Q110716513", "Q58897583", "Q51283145",
    "Q54670950", "Q91901000", "Q51283219", "Q70471362",
)


def _values(items: tuple[str, ...]) -> str:
    return " ".join(f"wd:{item}" for item in items)


def main_view_filter() -> str:
    """Return the frozen published scholarly-exclusion filter."""

    return f"""FILTER NOT EXISTS {{
  ?item p:P13046 ?publication_statement .
  ?publication_statement wikibase:rank ?publication_rank .
  FILTER(?publication_rank != wikibase:DeprecatedRank)
}}
FILTER NOT EXISTS {{
  ?item p:P31 ?scholarly_instance_statement .
  ?scholarly_instance_statement ps:P31 ?scholarly_instance ;
    wikibase:rank ?scholarly_instance_rank .
  FILTER(?scholarly_instance_rank != wikibase:DeprecatedRank)
  VALUES ?scholarly_instance {{ {_values(SCHOLARLY_P31_QIDS)} }}
}}"""


def candidate_query(*, limit: int = 100, offset: int = 0) -> str:
    """Construct a V7 candidate page with filtering before pagination."""

    if limit <= 0 or offset < 0:
        raise ValueError("limit must be positive and offset must be non-negative")
    return f"""PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX ps: <http://www.wikidata.org/prop/statement/>
PREFIX wikibase: <http://wikiba.se/ontology#>
SELECT ?item ?date WHERE {{
  ?item wdt:P585 ?date .
  {main_view_filter()}
}}
ORDER BY ASC(?date) ASC(?item)
LIMIT {limit}
OFFSET {offset}"""


def validate_initial_offset(offset: int) -> None:
    """Reject resumption from the historical V6 checkpoint."""

    if offset != V7_FORMAL_START_OFFSET:
        raise ValueError("V7 formal acquisition must start at offset 0")
