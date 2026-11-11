# Plan: `GET /progress` endpoint (in `my-coach/`)

## Context
You want to see your practice stats: how many rounds you've practised and your average
total score. These come from `data/results.json`, the file `data.save_result()` appends to.
This plan follows the house rules in `my-coach/CLAUDE.md`: file reads go through `data.py`,
response shapes are Pydantic models, routes stay thin, and tests never write to the real
`data/results.json`.

**Default chosen:** "rounds practised" means **the number of scored attempts**, so two
answers in the decomposition round count as 2. I picked this because it's the only reading
that pairs naturally with an *average* total. If you meant the number of distinct round types,
say so; that would only change one line.

## 1. Files to change

| File | Change |
|---|---|
| `app/models.py` | Add `ProgressResponse(BaseModel)` with `rounds_practised: int` and `average_total: float`. |
| `app/data.py` | Add `load_results() -> list[dict]`. It reads `DATA_DIR / "results.json"` and returns `[]` if the file is missing. Change the existing `save_result()` to call it, so the read logic lives in one place. |
| `app/main.py` | Add `@app.get("/progress") def get_progress() -> ProgressResponse`. It calls `data.load_results()`, counts the records, and averages `total`, rounded to 1 decimal place. It has an **explicit empty guard**: if there are no records, it returns `ProgressResponse(rounds_practised=0, average_total=0.0)` *before* any division happens. Include a one-line docstring. |
| `tests/test_progress.py` (new) | **One test** for the endpoint: `test_progress_empty_results_returns_zero`. It redirects the data folder to `tmp_path` (patching `app.data.DATA_DIR`), writes `[]` to `results.json`, calls `GET /progress`, and checks for a 200 status with `{"rounds_practised": 0, "average_total": 0.0}`. This test is the regression guard against dividing by zero. |

`scoring.py` is not touched.

## 2. Order
1. **Write the one test first** (`tests/test_progress.py`, the empty-results case). It fails now because the route doesn't exist.
2. `models.py`: add `ProgressResponse`.
3. `data.py`: add `load_results()` and refactor `save_result()` to use it. Run `pytest -q` to confirm the existing tests still pass.
4. `main.py`: add the route.
5. **Handle the empty case:** in `get_progress()`, check `if not results:` and return zeros *before* computing `sum(...) / count`. Only the non-empty path ever divides, so dividing by zero is impossible by construction rather than caught after the fact.
6. Run `pytest -q`. All 4 tests should pass (the 3 existing ones plus the new one).
7. Manual check: run `uvicorn app.main:app --reload`, open `/docs`, and try `GET /progress`.
8. Stop and show the diff. Commit only if you ask.

## 3. What could break or is easy to get wrong
- **Dividing by zero** when `results.json` is `[]`. That's the file's current state, so this is the case that runs first in practice.
- **Patching the wrong name in tests.** `data.py` does `from .config import DATA_DIR`, so the test must patch `app.data.DATA_DIR`. Patching `app.config.DATA_DIR` silently has no effect, and the test then reads and writes your real file.
- **Records with no fixed schema.** `save_result()` accepts any `dict`, so a record without a `"total"` key would cause a `KeyError` and a 500 error. For now I'd skip records that have no `total` rather than crash. Once `/score` is connected, it should write a fixed shape.
- **Missing or corrupt file.** A missing file is treated as "no results". A corrupt file is a real error and should give a clean 500 response, not a stack trace.
- **Int vs float.** Without rounding, an average like `12.333…` leaks into the response. With an empty list, Pydantic is fine whether the code passes `0` or `0.0`, but the code should pass `0.0` to be explicit.
- **Wrong averages from the existing bug.** Any total produced while the `compute_total()` bug is still there drops the first category. `/progress` will faithfully average numbers that are too low. That isn't a `/progress` bug, but it will look like one.

## 4. Riskiest assumption
**That `data/results.json` actually gets records containing a `total` field.** Right now nothing
writes to it: `POST /score` is still a stub and never calls `data.save_result()`, so the file
stays `[]` and `/progress` will always return `0` and `0.0`. Nobody has defined the record shape
either. The endpoint can be built and tested on its own with test data, but it only becomes
useful once `/score` saves `{round, question_id, total, max}`. That makes connecting `/score`
(Module 3) the real dependency.

## Verification
- Run `pytest -q`. The 3 existing tests and the 1 new progress test should pass.
- The single test covers only the empty case. The averaging math (e.g. totals 10 and 15 giving 12.5) is checked by hand, not by a test.
- Run `git diff`/`git status` on `my-coach` and check that `data/results.json` is unchanged after the tests run.
- In `/docs`, `GET /progress` should return `{"rounds_practised": 0, "average_total": 0.0}` with today's empty file.
