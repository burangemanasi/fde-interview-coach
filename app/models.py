"""Pydantic schemas — the shape of every request and response.

Pydantic validates data at the edges of the app, so the rest of the code can
trust the values it is handed.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class Question(BaseModel):
    """One interview question."""

    id: str
    round: str
    prompt: str


class ScoreRequest(BaseModel):
    """Body of POST /score."""

    round: str
    question_id: str
    answer: str


class CategoryScore(BaseModel):
    """The score for a single rubric category (0..5)."""

    name: str
    score: int
    max: int = 5
    feedback: str


class ScoreResponse(BaseModel):
    """The full scorecard returned by POST /score."""

    total: int
    max: int
    categories: list[CategoryScore]
    summary: str


class ProgressResponse(BaseModel):
    """Practice summary returned by GET /progress.

    The defaults are the "no practice yet" state, so ProgressResponse(rounds_practised=0)
    is the whole empty-case response.
    """

    rounds_practised: int
    average_total: float | None = None
    max_total: int = 20
    category_averages: dict[str, float] = Field(default_factory=dict)
    weakest_category: str | None = None
    focus_next: str | None = None
