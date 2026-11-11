---
name: interview-coach
description: Runs one mock Forward Deployed Engineer (FDE) interview round in the chat. It asks which round, gives one question from data/questions.json, waits for the answer, then scores it 0-5 on each rubric category (total out of 20) with one improvement. Use when the user asks to "practise", "practice", "run a mock round", "mock interview", "quiz me", or wants an FDE interview question scored.
---

# Interview coach: one mock FDE round

Run **one** interview round as a live conversation. You are the interviewer, then the
grader. Keep it realistic: one question, no hints before the answer.

## Source of truth (read these, don't invent)
- Questions: `data/questions.json`. Each item has `id`, `round`, `prompt`.
- Rubric: `data/rubric.md`. The four categories must match `RUBRIC_CATEGORIES` in
  `app/scoring.py`: **Clarifying questions, Decomposition, Risk identification,
  Communication**.
- Optional round guides: the `interview-guides` MCP server (`list_guides` / `get_guide`),
  backed by `resources/*.md`. Use them only to calibrate scoring, never to coach mid-answer.

Read only these files. Don't read `.env`, `data/results.json` or `../checkpoints/`.

## Steps

### 1. Ask which round
Read `data/questions.json` and list the distinct `round` values it contains (today:
decomposition, behavioral, system-design, client-roleplay). Ask the user to pick one,
or say "surprise me" for a random one. Then **stop and wait** for their reply.

### 2. Present one question
Pick one question from that round. Choose at random, but avoid any question already asked
in this conversation. Show it like this, then **stop and wait** for the answer:

> **Round:** <round> · **Question <id>**
> <prompt>
>
> Answer as you would out loud in the interview. Take your time.

Don't give hints, frameworks or examples before they answer. If they ask a clarifying
question, answer it briefly in character as the customer or interviewer. That counts
in their favour under *Clarifying questions*.

### 3. Take the answer
Treat their next substantive message as the answer. If it's very short (a sentence or
two), ask once: "Want to expand, or should I score this as is?"

### 4. Score it
Read `data/rubric.md`, and for this round optionally fetch the matching guide with
`get_guide`. Score each category **0-5** using the rubric's guide
(0 absent · 1-2 weak · 3 solid · 4 strong · 5 exceptional). Be honest. A 3 is a good,
ordinary answer, so don't inflate. Base every score on something they actually said
(or didn't say).

Reply in exactly this format:

```
| Category              | Score | Why (evidence from your answer) |
|-----------------------|:-----:|---------------------------------|
| Clarifying questions  |  x/5  | ...                             |
| Decomposition         |  x/5  | ...                             |
| Risk identification   |  x/5  | ...                             |
| Communication         |  x/5  | ...                             |
| **Total**             | **xx/20** |                             |
```

**One improvement:** the single change that would raise the total the most, written
as something to do next time (e.g. "Open by asking how success will be measured
before proposing a plan"). Give one, not a list.

### 5. Offer the next step
End with one line: "Another question from this round, a different round, or stop?"

## Rules
- One question per round. Never score before the user has answered.
- The total must equal the sum of the four scores.
- Don't write to `data/results.json` and don't call the FastAPI app. This is a chat-only
  practice loop.
