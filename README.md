# FDE Interview Prep Assistant

A small FastAPI app for practising Forward Deployed Engineer (FDE) interviews. It serves
mock interview questions by round, scores answers 0–5 on four rubric categories
(Clarifying questions, Decomposition, Risk identification, Communication; max 20), and
summarises your progress. Scoring runs offline (a mock scorer) by default, and uses
OpenAI only when an API key is set. The interactive `/docs` page is the UI.

## Endpoints

| Method | Path        | What it does                                                         |
|--------|-------------|----------------------------------------------------------------------|
| GET    | `/health`   | Liveness check                                                       |
| GET    | `/rounds`   | The interview round types (decomposition, behavioral, …)            |
| GET    | `/questions?round=…` | Questions for one round (404 for an unknown round)         |
| POST   | `/score`    | Score an answer. *Still a placeholder: it isn't wired to the scorer yet.* |
| GET    | `/progress` | Rounds practised, average total, weakest category, what to focus on next |

## Run it

```powershell
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload     # open http://127.0.0.1:8000/docs
pytest -q
```

Optional: copy `.env.example` to `.env` and set `OPENAI_API_KEY` for real scoring.

## How it was built

Built step by step with [Claude Code](https://claude.com/claude-code) as a learning project,
favouring clarity over cleverness:

- **Spec-driven:** [`specs/001-progress-endpoint/`](specs/001-progress-endpoint/) holds the
  spec for `/progress` and the 8 small tasks it was built in; each task was implemented,
  tested and reviewed on its own.
- **Tested:** 42 pytest tests. Tests that touch files use `tmp_path`, so the real `data/` is
  never modified, and no test calls the network.
- **Guardrails:** Claude Code hooks block reading `.env` and run ruff and mypy after every edit.
- **Agent tooling:**
  - an `interview-guides` MCP server ([`mcp/server.py`](mcp/server.py)) serves the
    interview guides in [`resources/`](resources/)
  - an `interview-coach` skill runs a mock round in chat and scores it out of 20
  - a `/report` command summarises progress from `data/results.json`

## Layout

```
app/        FastAPI routes, scoring, data access, Pydantic models, config
data/       questions.json, rubric.md, results.json (scored attempts)
resources/  interview guides (markdown), served by the MCP server
mcp/        the interview-guides MCP server
specs/      feature specs and task breakdowns
tests/      pytest suites
```
