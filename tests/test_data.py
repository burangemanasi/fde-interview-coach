"""Tests for file access in app/data.py (always against tmp_path, never real data/)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app import data


@pytest.fixture
def data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point data.py at an empty temp folder so tests never touch data/results.json."""
    monkeypatch.setattr(data, "DATA_DIR", tmp_path)
    return tmp_path


def test_load_results_missing_file_returns_empty(data_dir: Path) -> None:
    assert data.load_results() == []


def test_load_results_empty_list(data_dir: Path) -> None:
    (data_dir / "results.json").write_text("[]", encoding="utf-8")

    assert data.load_results() == []


def test_load_results_returns_records_unchanged(data_dir: Path) -> None:
    records = [{"total": 10, "categories": []}, {"total": 12, "round": "behavioral"}]
    (data_dir / "results.json").write_text(json.dumps(records), encoding="utf-8")

    assert data.load_results() == records


def test_load_results_invalid_json_raises(data_dir: Path) -> None:
    (data_dir / "results.json").write_text("{not json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        data.load_results()
