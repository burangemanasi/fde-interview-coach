"""Tests for the Pydantic schemas in app/models.py."""
from __future__ import annotations

from app.models import ProgressResponse


def test_progress_response_defaults_are_the_empty_case() -> None:
    # Spec 001, AC 1: the exact body /progress returns when there are no results.
    assert ProgressResponse(rounds_practised=0).model_dump() == {
        "rounds_practised": 0,
        "average_total": None,
        "max_total": 20,
        "category_averages": {},
        "weakest_category": None,
        "focus_next": None,
    }
