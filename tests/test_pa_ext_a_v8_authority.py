from __future__ import annotations

import sys
from pathlib import Path


EXP_DIR = Path(__file__).resolve().parents[1] / "experiments" / "paper_a_ext_a"
sys.path.insert(0, str(EXP_DIR))

from qlever_v7_main_view import main_view_filter  # noqa: E402
from qlever_v8_literal_main_view import (  # noqa: E402
    V7_HISTORICAL_NEXT_OFFSET,
    candidate_query,
    validate_initial_offset,
)


def test_v8_adds_only_literal_date_filter_before_pagination() -> None:
    query = candidate_query(limit=100, offset=0)
    assert "FILTER(ISLITERAL(?date))" in query
    assert query.index("FILTER(ISLITERAL(?date))") < query.index("ORDER BY")
    assert query.index("ORDER BY") < query.index("LIMIT") < query.index("OFFSET")
    assert main_view_filter() in query


def test_v8_rejects_v7_resume_offset() -> None:
    validate_initial_offset(0)
    try:
        validate_initial_offset(V7_HISTORICAL_NEXT_OFFSET)
    except ValueError:
        pass
    else:
        raise AssertionError("V8 accepted the V7 historical offset")
