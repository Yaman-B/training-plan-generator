# TPG: Personalized Training Plan Generator

A proof-of-concept tool that generates a personalized muscle-growth (hypertrophy) training
plan and hands the trainee a customized workout for today.

## What it does

- **Domain:** Paul Carter's training methodology, a three-phase periodization system:
  **Mass** (hypertrophy) → **Base Building** (work capacity, sub-maximal) →
  **Strong** (strength peaking). Hypertrophy only (no cardio or nutrition).
- **Planning Flow:** a trainee's questionnaire answers become a profile, which is
  decomposed into a yearly plan (three phase goals) → a monthly plan (month-by-month
  climb to each) → a weekly plan (each month broken into 4 weeks).
- **Session Flow:** turns the current plan into today's specific workout: the primary
  lift's target for the week, plus accessory exercises pulled from a curated exercise
  table (filtered by equipment access and injuries) and picked/prescribed by an LLM.
- **Structured data + free text.** The profile's enums (injury regions, equipment) drive a
  **deterministic** filter deciding which exercises are *allowed*; two optional free-text fields
  then guide the LLM's choice *within* that already-safe list, and can never widen it. Safety
  stays deterministic while the LLM adds nuance the enums can't express: ticking "shoulders"
  excludes everything shoulder-stressing, whereas *"shoulders ache on pressing; flyes are fine"*
  drops the presses but keeps the flyes.

## Setup

**Prerequisites:** Python 3.12+, [`uv`](https://docs.astral.sh/uv/), a local PostgreSQL
server, an Anthropic API key.

1. Install dependencies:
   ```
   uv sync
   ```
2. Create the database and load the schema + curated exercise data:
   ```
   createdb training_plan
   psql -d training_plan -f schema.sql
   psql -d training_plan -f scripts/seed_exercises.sql
   ```
   (`tpg/db.py` connects as `dbname="training_plan", user="postgres", host="localhost"`
   with no password. Adjust there if your local Postgres setup differs.)
3. Create a `.env` file at the repo root:
   ```
   ANTHROPIC_API_KEY=your-key-here
   ```
   Optionally add [Langfuse](https://cloud.langfuse.com) credentials to trace every LLM
   call (prompts, responses, tokens, cost, retries). Tracing switches itself off if these
   are absent, so they aren't required to run the app:
   ```
   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_SECRET_KEY=sk-lf-...
   LANGFUSE_BASE_URL=https://cloud.langfuse.com
   ```

## Running it

**Terminal questionnaire** (collects a profile and saves it):
```
uv run python -m scripts.run_questionnaire
```

**API server + web UI:**
```
uv run uvicorn tpg.main:app --reload
```
Open `http://127.0.0.1:8000/app/` for the web UI: an onboarding form, then a "This Week" view
showing every training day with today highlighted, and a "Your Plan" screen (linked from the
week view) showing the three yearly phases and the twelve monthly targets climbing to the goal.
Interactive API docs are at `http://127.0.0.1:8000/docs`.

## Tests

```
uv run pytest
```

74 tests, well under a second. They are **fast, offline and free**: no network, no database, no
API key, so they can be run constantly. Anything that talks to Claude or Postgres is a manual
smoke script in `scripts/` instead, which is why those aren't named `test_*` and must be run
with `-m` (`uv run python -m scripts.smoke_judge`).

They cover where bugs are silent rather than loud: every Pydantic validator, the deterministic
exercise filter, the calendar math, and the way the generators chain each step from the
previous one's result. The LLM is stubbed at the per-unit seam, so orchestration is tested
without ever calling the API.

## Judging plan quality

Validation proves a plan is well **formed** (phases in order, contiguous, 12 months, ending on
the goal). It says nothing about whether it's any **good**: a plan dumping 93% of the year's
gain into the first four months passes every check and is still nonsense.

`tpg/eval/judge.py` scores a plan on the two things validators can't see:

| Criterion | Question |
|---|---|
| `progression_rate` | Is the climb spread sensibly across the year, or crammed into one phase? |
| `phase_proportioning` | Do the three phase lengths suit this trainee's experience level? |

Each gets a 1-10 score plus a rationale. The plan's overall score is its **weakest** criterion,
computed rather than asked for, since an LLM asked to summarise its own scores will contradict
them.

`generate_reviewed_yearly_plan` then loops: generate, score, and if it falls short, hand the
planner its own plan plus the review and ask for better. It stops once the score clears the
target or the round limit runs out, returning the review alongside the plan so callers can tell
those two endings apart. The default target is 7 rather than 9 because this judge never awards
9 to anything; re-measure it if you edit the judge's prompt.

## API reference

| Method | Path | Description |
|---|---|---|
| `POST` | `/profile` | Create a profile |
| `GET` | `/profile/{profile_id}` | Read a profile |
| `POST` | `/profile/{profile_id}/plan` | Generate the full yearly + monthly + weekly plan in one call |
| `GET` | `/yearly-plan/{yearly_plan_id}` | Read a yearly plan |
| `GET` | `/monthly-plan/{monthly_plan_id}` | Read a monthly plan |
| `GET` | `/weekly-plan/{weekly_plan_id}` | Read a weekly plan |
| `POST` | `/weekly-plan/{weekly_plan_id}/sessions/week` | Generate a full workout for every training day of the current week (optional `target_date`); returns a 7-day grid with training/rest days marked. Used by the web UI. |
| `POST` | `/weekly-plan/{weekly_plan_id}/session/today` | Generate just today's session (optional `target_date`; returns `{"rest_day": true}` on a non-training day) |
| `GET` | `/session/{session_plan_id}` | Read a session plan |

## Project structure

```
tpg/
  schemas/     Pydantic models: profile, yearly/monthly/weekly plan, exercise, session
  planning/    Planning Flow generators (yearly, monthly, weekly)
  session/     Session Flow: eligibility filtering, scheduling, session generation
  eval/        LLM-as-judge: scores a yearly plan's quality (see Judging plan quality)
  llm.py       LLM provider abstraction (Claude / Ollama) + structured-output validation
  tracing.py   Langfuse `observe` decorator (a no-op when tracing is off)
  db.py        All Postgres access (save_*/load_* functions)
  main.py      FastAPI app
  questionnaire.py   Terminal questionnaire
scripts/
  run_questionnaire.py   Run the questionnaire and save a profile
  seed_exercises.sql     Curated exercise data
schema.sql     Hand-maintained snapshot of the Postgres schema
web/
  index.html   Onboarding form + plan-generation loading state
  week.html    "This Week" view: every training day of the week, today highlighted
  plan.html    "Your Plan": the yearly phases + monthly targets the LLM produced
  js/api.js    Fetch wrappers around the API above
```

Served directly by FastAPI (`StaticFiles` mounted at `/app`), no separate frontend server
or build step, plain HTML/CSS (Tailwind via CDN)/JS. Identity is a `profile_id` kept in the
browser's `localStorage`, there's no login.

## Observability (Langfuse)

Every LLM call is traced when Langfuse credentials are present. The Anthropic SDK is
auto-instrumented in `tpg/llm.py`, so calls are captured without touching any call site, and
`@observe()` decorators nest them into a readable tree. One request becomes one trace:

```
generate_week_api                         15.3s   $0.0122
└─ generate_week_sessions
   ├─ generate_todays_session             (training day)
   │  └─ generate_session_accessories
   │     └─ generate_structured
   │        └─ anthropic.chat             1007 tok  $0.0030
   └─ generate_todays_session             (rest day: no LLM call)
```

This also makes the retry loop in `generate_structured` visible: each attempt is its own call
under one span, so a validation failure and its recovery stop being invisible.

## Not yet built
- **A Profile view/edit page, workout logging/history, and real plan-generation progress
  reporting.** None of these have backend support yet.
