---
description: Summarise practice progress from data/results.json (rounds, average score, weakest category, next focus)
allowed-tools: Read
---

Read `data/results.json` and write a short progress report on my mock FDE interview
practice. Only read that file (and `data/rubric.md` if you need the category
definitions). Don't modify anything, and don't read `.env`.

## Expected data
`data/results.json` is a JSON list. Each entry is one scored attempt, shaped like the
app's `ScoreResponse`, possibly with extra fields:
- `total`: int, 0-20
- `categories`: list of `{ "name", "score" (0-5), "feedback" }`, using the four rubric
  categories: Clarifying questions, Decomposition, Risk identification, Communication
- optionally `round`, `question_id`, `answer`, `summary`

Skip any entry that has no usable `total` or `categories`, and say how many you skipped.
If `total` is missing but `categories` is present, use the sum of the category scores.

## If there are no results
If the file is missing, empty, or `[]` (or every entry was skipped), reply only:

> No practice results yet. Run a mock round (say "let's practise") or score an answer
> with `POST /score`, then try `/report` again.

## Otherwise, report exactly this

**Practice report**
- **Rounds practised:** N (and a per-round breakdown if `round` is present, e.g.
  "decomposition 3 · behavioral 1")
- **Average total:** X.X / 20
- **Weakest category:** <name>, averaging Y.Y / 5 (lowest mean score across all
  attempts; on a tie, name both)
- **Focus next:** one concrete, actionable habit aimed at the weakest category, based on
  its definition in `data/rubric.md` and, if present, the `feedback` text for that
  category. One sentence, not a list.

Round averages to one decimal place. Keep the whole report under ~10 lines. Do the
arithmetic carefully, because the numbers must match the file.
