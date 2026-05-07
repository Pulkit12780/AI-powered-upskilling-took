# upskillforjob — Project Overview

## What This Is

AI-powered career development tool. Users upload a resume PDF + specify a target role (+ optional location), and get back:
- Extracted current skills
- Required skills for the target role
- Skill gap analysis
- A week-by-week personalized learning path with curated course/YouTube recommendations

No auth, no database, no data persistence — resumes are processed in-memory only.

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI + Uvicorn |
| Templating | Jinja2 (server-rendered HTML) |
| Styling | Custom CSS (`static/css/style.css`) |
| PDF parsing | pypdf |
| LLM orchestration | LangGraph |
| LLM provider | OpenAI (`gpt-4o-mini` for most nodes, `gpt-4o` for gap analysis) |
| Structured output | Pydantic schemas + OpenAI `response_format` |
| Video search | YouTube Data API v3 |
| Rate limiting | slowapi (1 req/min on `/analyze`) |
| Hosting | Render.com |

## Project Structure

```
app/
  main.py          — FastAPI app, routes, rate limiting
  config.py        — pydantic-settings env config
  schemas.py       — Pydantic models (Skill, GapReport, LearningPath, etc.)
  pdf_loader.py    — PDF extraction with safe error handling
  youtube.py       — YouTube API client (lazy-loaded, cached)
  graph/
    state.py       — LangGraph GraphState TypedDict
    nodes.py       — Four workflow nodes (extract_skills, target_skills, gap_diff, recommend)
    workflow.py    — Graph assembly and compiled `graph` instance
  templates/
    base.html      — Base layout (nav, fonts, footer)
    index.html     — Home page with upload form
    results.html   — Results display (two-column: skills/gaps left, roadmap right)
static/
  css/style.css    — Application styles
tests/
  test_pdf_loader.py
render.yaml        — Render.com deployment config
requirements.txt
```

## Environment Variables

```
OPENAI_API_KEY=
YOUTUBE_API_KEY=
```

Set these manually in the Render dashboard (not synced from code). Locally, put them in `.env` (gitignored).

## LangGraph Workflow (linear)

```
extract_skills → target_skills → gap_diff → recommend → END
```

| Node | Model | What it does |
|---|---|---|
| `extract_skills` | gpt-4o-mini | Extracts skills + proficiency levels from resume text |
| `target_skills` | gpt-4o-mini | Returns industry-standard skills for the target role |
| `gap_diff` | gpt-4o | Compares current vs. required; location-aware analysis |
| `recommend` | gpt-4o-mini | Generates 2–4 week plan; fetches YouTube videos per query |

All nodes use OpenAI structured outputs with Pydantic models.

## Routes

| Method | Path | Description |
|---|---|---|
| GET | `/` | Home page with upload form |
| POST | `/analyze` | Main pipeline: PDF → LangGraph → results.html |

Rate limit: 1 request/minute on `/analyze`.

## Key Conventions

- **Template calls use the modern starlette signature**: `TemplateResponse(request, "name.html", context_dict)` — not the deprecated `TemplateResponse("name.html", {"request": request})`.
- `"request"` is NOT passed inside the context dict; starlette injects it automatically with the modern API.
- YouTube client is lazy-loaded on first use (`_get_client()` in `youtube.py`).
- YouTube failures in `recommend` are swallowed silently — the learning path still returns without videos.
- All course suggestions are flagged `"AI-suggested — verify before enrolling"` in the UI.

## Running Locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in API keys
uvicorn app.main:app --reload
```

## Deployment (Render)

Defined in `render.yaml`. Build installs deps with `--no-cache-dir --upgrade`. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Env vars must be set manually in the Render dashboard.

## Data Flow

```
POST /analyze
  → safe_extract(pdf_bytes)        # pdf_loader.py
  → graph.invoke({resume, role, location})
      → extract_skills             # GPT: SkillList
      → target_skills              # GPT: TargetSkillList
      → gap_diff                   # GPT: GapReport (location-aware)
      → recommend                  # GPT: LearningPath + YouTube search
  → results.html
```

## Phase 2 (not built yet)

Auth, database, saved sessions, review scraping, payments.
