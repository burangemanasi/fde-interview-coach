"""Scoring logic: turn a candidate's answer into a rubric-based scorecard.

>>> THIS FILE IS WHERE MOST OF THE WORKSHOP HAPPENS. <<<

In this START state, POST /score is not wired to any of it yet (see app/main.py).
During Module 3 you will, with Claude Code:
  * build    -> implement score_with_openai() and wire /score to score_answer()
  * test     -> write tests pinning  total == sum(category scores)
  * debug    -> those tests reveal the BUG in compute_total()      (marked below)
  * refactor -> clean up the messy format_scorecard()              (marked below)
"""
from __future__ import annotations

from .config import USE_MOCK
from .models import CategoryScore, ProgressResponse, ScoreResponse

# The four things every answer is scored on (mirrors data/rubric.md).
RUBRIC_CATEGORIES = [
    "Clarifying questions",
    "Decomposition",
    "Risk identification",
    "Communication",
]

# One habit to practise per rubric category, used by GET /progress as "focus next".
# Each tip turns that category's definition in data/rubric.md into an action.
# A lookup table (not if/else) so adding a category is a one-line change.
FOCUS_TIPS: dict[str, str] = {
    "Clarifying questions": (
        "Open by asking about the data, stakeholders, constraints and how success is measured."
    ),
    "Decomposition": (
        "Break the problem into a sequenced plan with one small, testable first deliverable."
    ),
    "Risk identification": (
        "Name your riskiest assumption and how you'd de-risk it: an eval, a pilot or a fallback."
    ),
    "Communication": (
        "Lead with the answer, then give two or three structured points a non-technical "
        "stakeholder can follow."
    ),
}


def score_mock(answer: str) -> list[CategoryScore]:
    """A tiny deterministic scorer used when there is no OpenAI key.

    Intentionally simple: longer, more structured answers score a little higher.
    The workshop is about the *workflow*, not about building a clever scorer.
    """
    length_signal = min(len(answer) // 120, 5)  # 0..5 by answer length
    structure_signal = min(answer.count("\n") + 1, 5)  # 0..5 by line breaks
    base = max(1, (length_signal + structure_signal) // 2)
    return [
        CategoryScore(name=name, score=base, feedback=f"Auto-estimate for '{name}'.")
        for name in RUBRIC_CATEGORIES
    ]


def compute_total(categories: list[CategoryScore]) -> int:
    """Sum the per-category scores into a single total (every category counts)."""
    return sum(category.score for category in categories)


# Summary bands as (minimum total, label), highest first. A total gets the first
# band whose minimum it reaches.
_SUMMARY_BANDS: list[tuple[int, str]] = [
    (16, "Strong answer"),
    (10, "Solid, with gaps"),
    (5, "Needs work"),
]
_LOWEST_SUMMARY = "Needs significant work"

# Full marks is an exact total, not a band: a (malformed) total above 20 is
# still just "Strong answer".
FULL_MARKS_TOTAL = 20
_FULL_MARKS_SUMMARY = "Strong answer - full marks"


def _summary_for(total: int) -> str:
    """Map a total score to its one-line summary."""
    if total == FULL_MARKS_TOTAL:
        return _FULL_MARKS_SUMMARY
    for minimum, label in _SUMMARY_BANDS:
        if total >= minimum:
            return label
    return _LOWEST_SUMMARY


def format_scorecard(categories: list[CategoryScore]) -> ScoreResponse:
    """Assemble the final ScoreResponse from the category scores."""
    total = compute_total(categories)
    return ScoreResponse(
        total=total,
        max=sum(c.max for c in categories),
        categories=categories,
        summary=_summary_for(total),
    )


def score_with_openai(answer: str) -> list[CategoryScore]:
    """Score using the real OpenAI API.

    *** STUB — Module 3 (build) ***
    Implement this to send the rubric (data/rubric.md) plus the candidate's
    answer to OpenAI using config.MODEL_ID, ask for JSON back, and parse it into
    one CategoryScore per rubric category. For now it just calls the mock so the
    app keeps working.
    """
    # TODO(workshop): call the OpenAI API here and parse the JSON response.
    return score_mock(answer)


def score_answer(answer: str) -> ScoreResponse:
    """Score one answer end to end (mock offline, OpenAI when a key is set)."""
    categories = score_with_openai(answer) if not USE_MOCK else score_mock(answer)
    return format_scorecard(categories)


def _is_number(value: object) -> bool:
    """True for int/float scores. bool is excluded because True is an int in Python."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_valid_record(record: object) -> bool:
    """A saved scorecard we can summarise: a dict with a numeric total and a categories list.

    results.json is hand-editable, so bad entries are skipped rather than crashing
    /progress. Extra fields (answer, round, ...) are fine and simply ignored.
    """
    return (
        isinstance(record, dict)
        and _is_number(record.get("total"))
        and isinstance(record.get("categories"), list)
    )


def _category_averages(records: list[dict]) -> dict[str, float]:
    """Mean score per rubric category across all records, rounded to 1 dp.

    Names outside RUBRIC_CATEGORIES and malformed category entries are ignored, and
    keys come out in rubric order, which is what makes the tie-break in
    _weakest_category() work.
    """
    scores: dict[str, list[float]] = {name: [] for name in RUBRIC_CATEGORIES}
    for record in records:
        for category in record["categories"]:
            if (
                isinstance(category, dict)
                and category.get("name") in scores
                and _is_number(category.get("score"))
            ):
                scores[category["name"]].append(category["score"])
    return {name: round(sum(s) / len(s), 1) for name, s in scores.items() if s}


def _weakest_category(averages: dict[str, float]) -> str | None:
    """The category with the lowest average, or None if there are none.

    min() returns the first of equal values, so a tie goes to whichever category
    comes first in RUBRIC_CATEGORIES. Compares the rounded averages the user sees.
    """
    if not averages:
        return None
    return min(averages, key=lambda name: averages[name])


def summarise_progress(records: list[dict]) -> ProgressResponse:
    """Turn saved scorecards into a practice summary for GET /progress.

    A pure function (no file I/O) so it can be tested with plain lists; the route
    passes in data.load_results(). No records is a normal state, not an error.
    """
    records = [record for record in records if _is_valid_record(record)]
    if not records:
        return ProgressResponse(rounds_practised=0)
    totals = [record["total"] for record in records]
    averages = _category_averages(records)
    weakest = _weakest_category(averages)
    return ProgressResponse(
        rounds_practised=len(totals),
        average_total=round(sum(totals) / len(totals), 1),
        category_averages=averages,
        weakest_category=weakest,
        focus_next=FOCUS_TIPS[weakest] if weakest else None,
    )
