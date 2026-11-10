# Spec 001: `GET /progress`

**Status:** Draft · **Date:** 2026-11-10

## Why
Practising only helps if you can see the trend. `/score` produces per-attempt scores, but
nothing turns them into "how am I doing and what should I work on?". `/progress` gives
that summary over HTTP, so it shows up in `/docs`, the app's only UI. It's the same
summary the `/report` slash command gives, but computed by code that can be tested
instead of by an LLM.

## What it returns
`200 OK` with a `ProgressResponse` (a new Pydantic model in `app/models.py`):

| Field               | Type                 | Meaning                                                   |
|---------------------|----------------------|-----------------------------------------------------------|
| `rounds_practised`  | `int`                | Number of valid scored attempts                           |
| `average_total`     | `float \| None`      | Mean `total`, rounded to 1 dp; `None` when there are none |
| `max_total`         | `int`                | Always `20`                                               |
| `category_averages` | `dict[str, float]`   | Mean score (1 dp) per rubric category; `{}` when empty    |
| `weakest_category`  | `str \| None`        | Category with the lowest mean; `None` when empty          |
| `focus_next`        | `str \| None`        | One fixed tip for `weakest_category`; `None` when empty   |

Example:
```json
{
  "rounds_practised": 3,
  "average_total": 11.7,
  "max_total": 20,
  "category_averages": {
    "Clarifying questions": 2.0, "Decomposition": 3.3,
    "Risk identification": 3.0, "Communication": 3.3
  },
  "weakest_category": "Clarifying questions",
  "focus_next": "Open by asking about data, stakeholders and how success is measured."
}
```

## What it reads
- `data/results.json`, only through a new `data.load_results()` in `app/data.py`.
  A missing file counts as `[]`.
- Each record is a saved `ScoreResponse` (`total`, `categories[].name/score`), possibly
  with extra fields, which are ignored.
- The category list comes from `scoring.RUBRIC_CATEGORIES`. The `focus_next` tips are a
  lookup table (one tip per category) in `scoring.py`.
- The endpoint is read-only: no writes, no OpenAI calls.

## Acceptance criteria
1. **Empty case:** if `results.json` is `[]` or missing, the response is `200` with
   `rounds_practised: 0`, `average_total: null`, `category_averages: {}`,
   `weakest_category: null`, `focus_next: null`. It does not return a 404.
2. **Counts:** `rounds_practised` equals the number of valid records.
3. **Average:** `average_total` is the mean of `total`, rounded to 1 dp.
4. **Per category:** `category_averages` has an entry for each `RUBRIC_CATEGORIES` name that
   appears in the data. Categories that aren't in the rubric are ignored.
5. **Weakest:** `weakest_category` is the lowest mean. On a tie, the first in
   `RUBRIC_CATEGORIES` order wins, so the result is deterministic.
6. **Focus:** `focus_next` is the lookup-table tip for `weakest_category`.
7. **Bad data:** records without a numeric `total` or a `categories` list are skipped
   without an error. If every record is bad, the response matches the empty case.
8. **Unreadable file:** if `results.json` isn't valid JSON, the response is `500` with a
   clear `detail` and no stack trace.
9. **Tests:** `tests/test_progress.py` covers criteria 1–8 using `tmp_path` and
   monkeypatch, and never touches the real `data/results.json`.

## Out of scope
- Writing results. Getting `/score` to call `save_result()` is a separate change, and
  until it ships, `/progress` always returns the empty case.
- Filtering (by round, date or question), pagination, and trends over time.
- LLM-generated advice: `focus_next` is a fixed string.
- Changes to the rubric, the `/report` command or the interview-coach skill.
