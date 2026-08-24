"""Offline query construction for the PA-EXT-A V8 literal-date amendment."""

from __future__ import annotations

from pathlib import Path

from qlever_v7_main_view import (
    QLEVER_ENDPOINT,
    RAW_GRAPH_SCOPE,
    main_view_filter,
)


EXP_DIR = Path(__file__).resolve().parent
V8_FORMAL_START_OFFSET = 0
V7_HISTORICAL_NEXT_OFFSET = 1000


def candidate_query(*, limit: int = 100, offset: int = 0) -> str:
    """Construct the V8 literal-date candidate page query.

    The only response-domain correction relative to V7 is the explicit
    literal-date filter. The frozen main-view exclusion remains before
    ordering and pagination.
    """

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
  FILTER(ISLITERAL(?date))
}}
ORDER BY ASC(?date) ASC(?item)
LIMIT {limit}
OFFSET {offset}"""


def validate_initial_offset(offset: int) -> None:
    """Reject V7 resumption and require a fresh V8 offset zero."""

    if offset != V8_FORMAL_START_OFFSET:
        raise ValueError("V8 formal acquisition must start at offset 0")


__all__ = [
    "EXP_DIR",
    "QLEVER_ENDPOINT",
    "RAW_GRAPH_SCOPE",
    "V8_FORMAL_START_OFFSET",
    "V7_HISTORICAL_NEXT_OFFSET",
    "candidate_query",
    "validate_initial_offset",
]
