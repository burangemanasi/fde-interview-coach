"""Tests for the scoring logic in app/scoring.py."""
from __future__ import annotations

import pytest

from app.models import CategoryScore
from app.scoring import FOCUS_TIPS, RUBRIC_CATEGORIES, compute_total, format_scorecard


def test_compute_total_sums_all_categories() -> None:
    categories = [
        CategoryScore(name=name, score=3, feedback="ok") for name in RUBRIC_CATEGORIES
    ]
    assert len(categories) == 4

    assert compute_total(categories) == 12


# Pins the summary band for every boundary, plus out-of-range totals the scorer
# doesn't validate (an LLM could return them). 21 is deliberately NOT "full marks":
# full marks means a total of exactly 20.
@pytest.mark.parametrize(
    ("total", "summary"),
    [
        (-1, "Needs significant work"),
        (0, "Needs significant work"),
        (4, "Needs significant work"),
        (5, "Needs work"),
        (9, "Needs work"),
        (10, "Solid, with gaps"),
        (15, "Solid, with gaps"),
        (16, "Strong answer"),
        (19, "Strong answer"),
        (20, "Strong answer - full marks"),
        (21, "Strong answer"),
    ],
)
def test_format_scorecard_summary_bands(total: int, summary: str) -> None:
    categories = [CategoryScore(name="Only", score=total, feedback="ok")]

    result = format_scorecard(categories)

    assert result.total == total
    assert result.summary == summary


def test_format_scorecard_max_is_sum_of_category_maxes() -> None:
    categories = [
        CategoryScore(name=name, score=3, feedback="ok") for name in RUBRIC_CATEGORIES
    ]

    result = format_scorecard(categories)

    assert result.max == 20
    assert result.categories == categories


def test_focus_tips_cover_exactly_the_rubric_categories() -> None:
    # If a category is added or renamed, this fails until FOCUS_TIPS is updated too.
    assert set(FOCUS_TIPS) == set(RUBRIC_CATEGORIES)


def test_focus_tips_are_non_empty() -> None:
    assert all(isinstance(tip, str) and tip.strip() for tip in FOCUS_TIPS.values())
