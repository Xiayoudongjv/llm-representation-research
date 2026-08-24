"""Offline tests for the prospective PA-EXT-A V7 authority."""

from __future__ import annotations

from experiments.paper_a_ext_a import qlever_v7_main_view as v7


def test_filter_precedes_order_and_pagination() -> None:
    query = v7.candidate_query(limit=100, offset=0)
    assert query.index("FILTER NOT EXISTS") < query.index("ORDER BY")
    assert query.index("ORDER BY") < query.index("LIMIT") < query.index("OFFSET")


def test_filter_encodes_published_rule_without_p279_ancestry() -> None:
    text = v7.main_view_filter()
    assert "p:P13046" in text
    assert "p:P31" in text
    assert "wikibase:DeprecatedRank" in text
    assert "P279" not in text


def test_v7_initial_offset_is_zero_and_v6_checkpoint_is_rejected() -> None:
    v7.validate_initial_offset(0)
    try:
        v7.validate_initial_offset(v7.HISTORICAL_V6_CHECKPOINT_OFFSET)
    except ValueError:
        pass
    else:
        raise AssertionError("V6 checkpoint must not be accepted as V7 start")
