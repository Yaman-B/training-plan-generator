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
  **deterministic** filter that decides which exercises are *allowed*. Two optional free-text
  fields (`goal_description`, `injury_description`) are then fed to the **LLM prompts**, which
  guide the choice *within* that already-safe list. So safety stays deterministic, while the
  LLM handles nuance the enums can't express: ticking "shoulders" excludes every
  shoulder-stressing exercise, whereas writing *"shoulders ache on pressing; flyes are fine"*
  lets the model avoid the presses while keeping the flyes.

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
uv run python scripts/run_questionnaire.py
```

**API server + web UI:**
```
uv run uvicorn tpg.main:app --reload
```
Open `http://127.0.0.1:8000/app/` for the web UI: an onboarding form, then a "This Week" view
showing every training day of the current week with today highlighted, and a "Your Plan"
screen (linked from the week view) that surfaces what the LLM actually produced — the three
yearly phases and the twelve monthly targets climbing to the goal. Interactive API docs (try
requests directly in the browser) are at `http://127.0.0.1:8000/docs`.

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
auto-instrumented in `tpg/llm.py`, so calls are captured without touching any call site,
and `@observe()` decorators on the generator functions nest those calls into a readable
tree. One plan generation becomes a single trace:

```
generate_week_api                         15.3s   $0.0122
└─ generate_week_sessions
   ├─ generate_todays_session             (training day)
   │  └─ generate_session_accessories
   │     └─ generate_structured
   │        └─ anthropic.chat             1007 tok  $0.0030
   └─ generate_todays_session             (rest day: no LLM call)
```

Most usefully, the retry-with-feedback loop in `generate_structured` becomes visible —
each attempt shows up as its own call under one span, so a validation failure and its
recovery are no longer invisible.

## Not yet built

- **LangGraph** (orchestration). Deliberately deferred; still an open question whether it
  adds real value here, since it would mostly formalize control flow that already works
  today as plain Python.
- **A Profile view/edit page, workout logging/history, and real plan-generation progress
  reporting.** None of these have backend support yet.
