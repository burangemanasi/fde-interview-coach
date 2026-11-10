# Tasks 001: `GET /progress`

Built from [spec.md](spec.md). Each task is a single change of one or two files with its
own tests, done in order. After each one, run `pytest -q` and check it passes, then
review the diff. "AC n" means acceptance criterion n in the spec.

Every test that touches files uses `tmp_path` and monkeypatches `app.data.DATA_DIR`.
Tests never read or write the real `data/results.json`.

---

## T1: `data.load_results()`
**Files:** `app/data.py`, `tests/test_data.py` (new)

Add `load_results() -> list[dict]`. It reads `DATA_DIR / "results.json"` and returns
`[]` if the file is missing. Invalid JSON is not caught here; `json.JSONDecodeError`
propagates to the caller.

**Tests**
- A missing file returns `[]`.
- A file with `[]` returns `[]`.
- A file with two records returns both, unchanged.
- A file with invalid JSON raises `json.JSONDecodeError`.

**Done when:** the tests pass and nothing outside `data.py` opens the file.

---

## T2: the `ProgressResponse` model
**Files:** `app/models.py`, `tests/test_models.py` (new)

Add `ProgressResponse` with the fields from the spec table. `max_total` defaults to `20`.
The optional fields default to `None`, and `category_averages` defaults to `{}`.

**Tests**
- `ProgressResponse(rounds_practised=0)` serialises to exactly the empty-case JSON
  from AC 1.

**Done when:** the model exists and isn't used anywhere yet, so nothing else changes.

---

## T3: the `FOCUS_TIPS` lookup table
**Files:** `app/scoring.py`, `tests/test_score.py`

Add `FOCUS_TIPS: dict[str, str]`, a constant with one short tip per rubric category.
Write each tip from that category's definition in `data/rubric.md`.

**Tests**
- `set(FOCUS_TIPS) == set(RUBRIC_CATEGORIES)`, so the two lists can't drift apart.
- Every tip is a non-empty string.

**Done when:** the tests pass and the rest of the scoring behaviour is unchanged.

---

## T4: `summarise_progress()`, counts and average
**Files:** `app/scoring.py`, `tests/test_progress.py` (new)

Add `summarise_progress(records: list[dict]) -> ProgressResponse`. This is a pure
function with no I/O. In this task it fills in only `rounds_practised` and
`average_total` (1 dp), and leaves the category fields at their defaults.

**Tests:** AC 1 (empty list), AC 2, AC 3. Include one average that needs rounding, e.g.
totals 10, 11, 14 give `11.7`.

---

## T5: `summarise_progress()`, categories, weakest and focus
**Files:** `app/scoring.py`, `tests/test_progress.py`

Fill in `category_averages`, `weakest_category` and `focus_next`.

**Tests**
- AC 4: averages per category, and a category that isn't in the rubric is ignored.
- AC 5: a clear lowest category; a tie resolved by `RUBRIC_CATEGORIES` order.
- AC 6: `focus_next == FOCUS_TIPS[weakest_category]`.

---

## T6: `summarise_progress()`, skipping bad records
**Files:** `app/scoring.py`, `tests/test_progress.py`

Skip records that have no numeric `total` or no `categories` list.

**Tests (AC 7)**
- A mix of good and bad records counts only the good ones.
- All bad records give the empty-case response.
- Records with extra fields (`answer`, `round`, …) still count.

---

## T7: the `GET /progress` route
**Files:** `app/main.py`, `tests/test_progress.py`

Add a thin route: `summarise_progress(data.load_results())`. If it raises
`json.JSONDecodeError`, return `HTTPException(500, detail="results.json is not valid JSON")`.

**Tests** (using `TestClient` and a monkeypatched `DATA_DIR`)
- AC 1 over HTTP: no file → `200` with the empty-case body.
- One end-to-end case: a fixture file with 2–3 records → the expected body.
- AC 8: invalid JSON → `500` with that `detail`, and no traceback in the body.

**Done when:** `/progress` appears in `/docs`, and this test plus the earlier ones
together cover AC 9.

---

## T8: final checks
**Files:** none, unless the checks find something

Run `ruff check .`, `mypy app`, and `pytest -q`, then confirm `git status` shows that
`data/results.json` hasn't changed. Check every item in the spec off against a test.
