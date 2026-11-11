# CLAUDE.md — FDE Interview Prep Assistant

## What we're building
A small FastAPI app that runs mock Forward Deployed Engineer interviews and scores
answers 0–5 on four rubric categories (max 20). It's a learning project: favour
**clarity over cleverness**, so every line should be easy to explain in an interview.
The `/docs` page is the only UI.

## Stack
- Python 3.11+, **FastAPI** + uvicorn, **Pydantic v2**
- Data: plain **JSON/markdown files** in `data/`, no database
- Scoring: an offline **mock** by default; **OpenAI** only when `OPENAI_API_KEY` is set
  (the model id lives in one constant, `app/config.MODEL_ID`)
- Tests: **pytest** + FastAPI `TestClient`
- Tooling (from Module 4): ruff, mypy. MCP server (from Module 5): fastmcp

## Project layout
- `app/main.py`: HTTP routes only. Keep them thin: validate, delegate, return.
- `app/scoring.py`: all scoring logic, the rubric categories, and LLM prompts
- `app/data.py`: the only module that reads or writes files in `data/`
- `app/models.py`: every Pydantic request/response schema
- `app/config.py`: paths, env vars, `MODEL_ID`, `USE_MOCK`
- `data/`: `questions.json` (question bank), `rubric.md`, `results.json` (scored attempts)
- `resources/`: interview guides (markdown), served by the MCP server in Module 5
- `tests/`: pytest suites, one file per area (`test_basic.py`, `test_score.py`, …)

## Conventions
- Type-hint everything. Every module starts with `from __future__ import annotations`.
- Every module and public function gets a short docstring saying *why*, not just what.
- Keep functions small and named for what they do. Prefer a lookup table over nested if/else.
- Request and response shapes are Pydantic models in `models.py`. Don't return bare dicts
  for new endpoints unless the shape is trivial.
- File I/O goes through `data.py`. Routes and scoring never open files directly.
- LLM prompts are named constants in `scoring.py`, never inline strings.
- Any OpenAI failure falls back to `score_mock()`. The app must never crash because
  scoring failed.
- Errors go to the client as `HTTPException` with a clear `detail`. Never leak a stack trace.
- The rubric categories in `scoring.RUBRIC_CATEGORIES` must match `data/rubric.md`.

## Guardrails for you, the agent
- **This is a learning project.** Don't read, copy, or diff against
  `../checkpoints/*` (the solution snapshots) unless I ask you to.
- Show a plan before any multi-file change, and the diff before applying it.
- Build in small steps: one change, then run, then test. Commit only when I ask.
- Debugging: write a failing test that reproduces the bug, list ranked hypotheses,
  and only then change code.
- Refactoring: run the tests before and after. Behaviour must not change.
- Tests never touch the network (keep `USE_MOCK` on) and never leave entries in
  `data/results.json` (use `tmp_path`/monkeypatch).
- Never read, print, or commit `.env` or any API key. Only edit `.env.example`.
- Don't add dependencies without asking. If I agree, add them to `requirements.txt`.
- Commands run on Windows. Give PowerShell-friendly versions.

## How to run
```
python -m venv .venv
.venv\Scripts\activate            # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload     # open http://127.0.0.1:8000/docs
pytest -q
```
Optional: copy `.env.example` to `.env` and set `OPENAI_API_KEY` for real scoring.
