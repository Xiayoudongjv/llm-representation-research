import pytest

from src.experiment_io import (
    assert_required_columns,
    load_json,
    read_csv,
    safe_float,
    save_json,
    validate_csv_rows,
    write_csv,
)


def test_save_json_load_json_round_trip(tmp_path):
    path = tmp_path / "nested" / "data.json"
    data = {"message": "你好", "values": [1, 2, 3]}
    save_json(data, path)
    assert load_json(path) == data


def test_write_csv_read_csv_round_trip(tmp_path):
    path = tmp_path / "nested" / "data.csv"
    rows = [{"id": "a", "score": "1.5"}, {"id": "b", "score": "2.0"}]
    write_csv(path, ["id", "score"], rows)
    assert read_csv(path) == rows


def test_validate_csv_rows_passes_for_valid_rows():
    validate_csv_rows(["id", "value"], [{"id": "a", "value": "1"}])


def test_validate_csv_rows_fails_for_missing_key():
    with pytest.raises(ValueError, match="missing keys"):
        validate_csv_rows(["id", "value"], [{"id": "a"}])


def test_validate_csv_rows_fails_for_extra_key():
    with pytest.raises(ValueError, match="extra keys"):
        validate_csv_rows(["id"], [{"id": "a", "extra": "x"}])


def test_assert_required_columns_passes():
    assert_required_columns([{"id": "a", "value": "1"}], ["id", "value"])


def test_assert_required_columns_fails():
    with pytest.raises(ValueError, match="missing required columns"):
        assert_required_columns([{"id": "a"}], ["id", "value"])


def test_safe_float_handles_valid_empty_none_and_invalid_values():
    assert safe_float("1.5") == 1.5
    assert safe_float("") is None
    assert safe_float(None) is None
    assert safe_float("bad") is None
