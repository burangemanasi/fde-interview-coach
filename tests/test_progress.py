"""Tests for GET /progress and scoring.summarise_progress() (spec 001)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import data
from app.main import app
from app.models import ProgressResponse
from app.scoring import FOCUS_TIPS, summarise_progress


def record(total: int, scores: dict[str, int] | None = None) -> dict:
    """A saved scorecard shaped like ScoreResponse; `scores` maps category -> 0..5."""
    categories = [
        {"name": name, "score": score, "feedback": "ok"}
        for name, score in (scores or {}).items()
    ]
    return {"total": total, "categories": categories}


def all_four(clarifying: int, decomposition: int, risk: int, communication: int) -> dict:
    """A record scoring all four rubric categories, with a matching total."""
    return record(
        clarifying + decomposition + risk + communication,
        {
            "Clarifying questions": clarifying,
            "Decomposition": decomposition,
            "Risk identification": risk,
            "Communication": communication,
        },
    )


# --- AC 1: empty case -------------------------------------------------------


def test_no_records_is_the_empty_case() -> None:
    assert summarise_progress([]) == ProgressResponse(rounds_practised=0)


# --- AC 2: counts -----------------------------------------------------------


def test_rounds_practised_counts_records() -> None:
    result = summarise_progress([record(8), record(12), record(16)])

    assert result.rounds_practised == 3


# --- AC 3: average total ----------------------------------------------------


def test_average_total_single_record() -> None:
    assert summarise_progress([record(12)]).average_total == 12.0


def test_average_total_rounds_to_one_decimal() -> None:
    # (10 + 11 + 14) / 3 = 11.666... -> 11.7
    assert summarise_progress([record(10), record(11), record(14)]).average_total == 11.7


def test_max_total_is_twenty() -> None:
    assert summarise_progress([record(12)]).max_total == 20


# --- AC 4: per-category averages --------------------------------------------


def test_category_averages_per_rubric_category() -> None:
    result = summarise_progress([all_four(2, 3, 3, 4), all_four(3, 4, 2, 4)])

    assert result.category_averages == {
        "Clarifying questions": 2.5,
        "Decomposition": 3.5,
        "Risk identification": 2.5,
        "Communication": 4.0,
    }


def test_category_averages_round_to_one_decimal() -> None:
    # Clarifying: (1 + 2 + 2) / 3 = 1.666... -> 1.7
    records = [all_four(1, 3, 3, 3), all_four(2, 3, 3, 3), all_four(2, 3, 3, 3)]

    assert summarise_progress(records).category_averages["Clarifying questions"] == 1.7


def test_category_not_in_rubric_is_ignored() -> None:
    result = summarise_progress([record(5, {"Decomposition": 3, "Charisma": 2})])

    assert result.category_averages == {"Decomposition": 3.0}
    assert result.weakest_category == "Decomposition"


# --- AC 5: weakest category -------------------------------------------------


def test_weakest_category_is_lowest_average() -> None:
    result = summarise_progress([all_four(4, 4, 1, 3), all_four(4, 3, 2, 3)])

    assert result.weakest_category == "Risk identification"


def test_weakest_category_tie_goes_to_rubric_order() -> None:
    # Communication is listed first in the record, but Decomposition comes first
    # in RUBRIC_CATEGORIES, so it wins the tie.
    tied = record(10, {"Communication": 2, "Clarifying questions": 4,
                       "Decomposition": 2, "Risk identification": 2})

    assert summarise_progress([tied]).weakest_category == "Decomposition"


def test_records_without_categories_have_no_weakest() -> None:
    result = summarise_progress([record(12)])

    assert result.category_averages == {}
    assert result.weakest_category is None
    assert result.focus_next is None


# --- AC 6: focus next -------------------------------------------------------


def test_focus_next_is_the_tip_for_the_weakest_category() -> None:
    result = summarise_progress([all_four(1, 4, 4, 4)])

    assert result.weakest_category == "Clarifying questions"
    assert result.focus_next == FOCUS_TIPS["Clarifying questions"]


# --- AC 7: bad records are skipped ------------------------------------------

BAD_RECORDS: list = [
    {"categories": []},                    # no total
    {"total": "12", "categories": []},     # total is not a number
    {"total": True, "categories": []},     # bool is not a score
    {"total": 12},                         # no categories
    {"total": 12, "categories": "lots"},   # categories is not a list
    "not a record",                        # not a dict at all
    None,
]


def test_bad_records_are_skipped_good_ones_counted() -> None:
    result = summarise_progress([all_four(2, 3, 3, 4), *BAD_RECORDS, all_four(4, 3, 3, 4)])

    assert result.rounds_practised == 2
    assert result.average_total == 13.0


def test_all_bad_records_is_the_empty_case() -> None:
    assert summarise_progress(BAD_RECORDS) == ProgressResponse(rounds_practised=0)


def test_extra_fields_still_count() -> None:
    extra = {**all_four(3, 3, 3, 3), "answer": "...", "round": "behavioral", "summary": "ok"}

    assert summarise_progress([extra]).rounds_practised == 1


def test_malformed_category_entries_are_ignored() -> None:
    good = {"name": "Decomposition", "score": 3, "feedback": "ok"}
    bad = ["oops", {"name": "Communication"}, {"name": "Communication", "score": "high"}]

    result = summarise_progress([{"total": 3, "categories": [good, *bad]}])

    assert result.rounds_practised == 1
    assert result.category_averages == {"Decomposition": 3.0}


# --- GET /progress over HTTP (AC 1, AC 8, end to end) -----------------------

client = TestClient(app)


@pytest.fixture
def data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point data.py at an empty temp folder so tests never touch data/results.json."""
    monkeypatch.setattr(data, "DATA_DIR", tmp_path)
    return tmp_path


def test_progress_endpoint_no_file_is_empty_case(data_dir: Path) -> None:
    resp = client.get("/progress")

    assert resp.status_code == 200
    assert resp.json() == ProgressResponse(rounds_practised=0).model_dump()


def test_progress_endpoint_end_to_end(data_dir: Path) -> None:
    records = [all_four(2, 3, 3, 4), all_four(1, 4, 2, 4), all_four(3, 4, 3, 4)]
    (data_dir / "results.json").write_text(json.dumps(records), encoding="utf-8")

    resp = client.get("/progress")

    assert resp.status_code == 200
    assert resp.json() == {
        "rounds_practised": 3,
        "average_total": 12.3,  # (12 + 11 + 14) / 3
        "max_total": 20,
        "category_averages": {
            "Clarifying questions": 2.0,
            "Decomposition": 3.7,
            "Risk identification": 2.7,
            "Communication": 4.0,
        },
        "weakest_category": "Clarifying questions",
        "focus_next": FOCUS_TIPS["Clarifying questions"],
    }


def test_progress_endpoint_invalid_json_is_clear_500(data_dir: Path) -> None:
    (data_dir / "results.json").write_text("{not json", encoding="utf-8")

    resp = client.get("/progress")

    assert resp.status_code == 500
    assert resp.json() == {"detail": "results.json is not valid JSON"}
    assert "Traceback" not in resp.text
