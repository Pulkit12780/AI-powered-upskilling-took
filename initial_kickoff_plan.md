# upskillforjob.com — Week 1 Kickoff Plan

## Context

**The problem:** People who want to switch roles or jobs often don't know how to upskill — what to learn, in what order, or which courses are worth their time. Generic "top 10 courses" lists don't account for what they already know.

**The solution:** A web app at **upskillforjob.com** where a user uploads their resume + a target role, and gets a personalized learning path: skill-gap analysis + curated course/YouTube recommendations.

**Why now / scope of this plan:** The user wants to ship a v1 in **1 week with 2 hours/day (~14 hours total)**. This plan deliberately cuts auth, database, and review-scraping from week 1 to make that timeline realistic. Those are phase 2.

**Intended week-1 outcome:** A working local app where you (and a couple of testers via ngrok) can upload a resume + role and get a personalized learning path. No login, no DB, no payment. Hosting decision comes after local validation.

---

## Tech stack (v1)

| Layer | Choice | Why |
|---|---|---|
| Backend | **FastAPI** (Python) | User knows Python; fastest "real HTML" path with templating |
| Templating | **Jinja2** | Bundled with FastAPI; server-rendered HTML matches user's HTML preference |
| Styling | **Tailwind via CDN** | Zero build step for v1; swap to compiled later if needed |
| PDF parsing | **pypdf** | Mature, pure-Python, handles most resume PDFs (text-based only; scanned PDFs fail gracefully) |
| LLM orchestration | **LangGraph** (or 4 plain async functions) | User already knows it; graph fits the multi-node workflow — but 4 sequential functions work just as well for a linear chain |
| LLM provider | **OpenAI API** (gpt-4o-mini default, gpt-4o for skill-gap reasoning) | Fast, cheap, reliable structured output via `response_format` |
| Structured output | **Pydantic** schemas | Reliable JSON from LLMs |
| YouTube data | **YouTube Data API v3** | Free quota (10K units/day), official, no scraping risk |
| Course data (v1) | **LLM-suggested** Coursera/Udemy courses with disclaimer | Real scraping is phase 2 |
| Deploy | **TBD — evaluate after local v1 works** | Ship locally first; pick hosting once the product is validated |

**Explicitly cut from v1 (phase 2):**
- Google OAuth / phone auth
- Postgres user database
- Skills dropdown (LLM extracts from resume; user can edit)
- Coursera/Udemy scraping
- Review-based ranking

---

## Project structure to create

```
upskillforjob/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, routes
│   ├── config.py               # API keys, settings
│   ├── pdf_loader.py           # pypdf-based resume text extraction
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py            # LangGraph state definition
│   │   ├── nodes.py            # extract_skills, target_skills, gap_diff, recommend
│   │   └── workflow.py         # graph wiring
│   ├── schemas.py              # Pydantic models (Skill, GapReport, CourseRec, LearningPath)
│   ├── youtube.py              # YouTube Data API client
│   └── templates/
│       ├── base.html           # Tailwind CDN, layout
│       ├── index.html          # Upload form
│       └── results.html        # Learning path render
├── static/
│   └── (favicon, any custom CSS)
├── tests/

│   └── test_pdf_loader.py      # smoke test for PDF parsing
├── .env.example                # OPENAI_API_KEY, YOUTUBE_API_KEY
├── .gitignore
├── requirements.txt
├── render.yaml                 # Render deploy config
└── README.md
```

---

## Day-by-day execution (14 hours)

### Day 1 (2h) — Scaffold + PDF upload
- `git init`, virtualenv, `requirements.txt` (fastapi, uvicorn, jinja2, pypdf, python-multipart, pydantic, openai, langgraph, google-api-python-client, python-dotenv, slowapi)
- `app/main.py`: `GET /` renders `index.html` with upload form (file input + target role text input)
- `POST /analyze` accepts multipart, extracts text via `pdf_loader.py`, returns parsed text in a debug page
- `pdf_loader.py`: if `extract_text()` returns empty string, return a user-facing error: "We couldn't read your PDF — try copy-pasting your resume as text." Do not fail silently.
- Reject non-PDF uploads at the route level with a friendly message
- Tailwind CDN in `base.html`; basic landing page copy
- **Done when:** `uvicorn app.main:app --reload` runs locally; uploading a PDF + role echoes back the parsed resume text; uploading a blank/scanned PDF shows the fallback message

### Day 2 (2h) — Pipeline nodes 1 & 2
- `schemas.py`: `Skill`, `SkillList`, `GapReport`
- Implement as either LangGraph nodes OR plain async functions — pick whichever you're more confident shipping fast. The chain is linear (no cycles, no branching), so both work equally well. If LangGraph setup takes more than 30 min, switch to 4 async functions and don't look back.
- `nodes.py` (or `pipeline.py`):
  - `extract_current_skills(resume_text) -> SkillList` (Haiku 4.5, structured output)
  - `generate_required_skills(target_role) -> SkillList` (Haiku 4.5, structured output)
- Wire into `/analyze`; render both lists on results page
- **Done when:** uploading a resume + "Senior Product Manager" returns two visible skill lists

### Day 3 (2h) — Gap diff node + results UI design
- `gap_diff(current, required) -> GapReport` (Sonnet 4.6 — reasoning-heavy step)
- Categorize gaps: `must_learn`, `nice_to_have`, `already_have`
- **Results layout decision (make this call on Day 3):** The output format IS the product — users judge the whole thing by how results feel. Two options:
  - *Three columns* (gaps / nice-to-have / strengths): easy to build, shows breadth
  - *Vertical week-by-week roadmap* ("Week 1: foundations → Week 2: intermediate → Week 3: advanced"): implies sequence and progress, which is the actual value being delivered — **recommended**
- Whichever layout you pick, commit to it on Day 3 so Day 5 polish doesn't redesign from scratch
- **Done when:** results page shows clear "you have X, you need Y, your gaps are Z" in the chosen layout

### Day 4 (2h) — Recommendations + YouTube enrichment
- Google Cloud project should already be set up from pre-work (see below) — just retrieve your key
- `youtube.py`: `search_videos(query, max_results=3)` returning title, channel, view_count, url
- `recommend_courses(gap_report) -> LearningPath` node:
  - LLM suggests Coursera/Udemy courses per gap skill (mark as "AI-suggested, verify")
  - For each gap skill, fetch top 2-3 YouTube videos via API
- **Done when:** results page shows weekly learning plan with real YouTube links

### Day 5 (2h) — Polish + rate limiting
- Loading spinner during `/analyze` (HTMX or vanilla JS fetch)
- Error states: bad PDF, empty role, API failure, scanned/image PDF
- Mobile-responsive Tailwind classes
- Privacy disclaimer ("we don't store your resume")
- **Rate limiting:** add 1 analysis per IP per minute — use `slowapi` (2-line FastAPI middleware) or an in-memory `dict` counter. Without this, one person or bot can drain your Anthropic credits overnight.
- **Done when:** site looks shippable; tested with 3 different resumes; spamming /analyze from the same IP is blocked after the first request

### Day 6 (2h) — End-to-end QA + local user testing
- Full run-through with 3 different resumes (software engineer, marketing, blank/scanned PDF)
- Fix any bugs surfaced in Day 5 polish
- Share localhost via **ngrok** (`ngrok http 8000`) with 2–3 friends for quick feedback without deploying
- Capture: did they understand what to do? Did recs feel relevant? What broke?
- **Done when:** 3 resumes produce sensible results; ngrok link works for at least one external tester

### Day 7 (2h) — Evaluate hosting + decide next step
- Review feedback from Day 6 testers
- Fix top 2–3 issues
- **Hosting decision:** if product is working well and worth sharing more widely, evaluate options (Render free tier, Railway, Fly.io, self-host) — pick based on budget and expected traffic
- **Done when:** you've decided whether to ship publicly and have a concrete next step

---

## Critical files (will be created, not modified — greenfield)

All paths below are new; this is a greenfield project.

- `app/main.py` — FastAPI routes
- `app/pdf_loader.py` — `pypdf` wrapper
- `app/graph/nodes.py` — LangGraph nodes (the LLM logic lives here)
- `app/graph/workflow.py` — graph wiring
- `app/schemas.py` — Pydantic models for structured output
- `app/youtube.py` — YouTube Data API client
- `app/templates/index.html` + `results.html` + `base.html` — UI
- `render.yaml` — deploy config

**OpenAI SDK patterns to apply:**
- Use `response_format={"type": "json_schema", "json_schema": {...}}` for structured output — no manual JSON parsing
- Default to `gpt-4o-mini` for extract/recommend nodes (cheap, fast); use `gpt-4o` for the gap-diff node (reasoning-heavy)
- Set `OPENAI_API_KEY` in `.env`; never hardcode it

---

## Verification (end-to-end)

**Local (after each day):**
1. `uvicorn app.main:app --reload`
2. Upload a real resume PDF + a target role
3. Confirm the day's deliverable appears correctly

**Day 5 manual QA matrix:**
| Resume | Target role | Expected |
|---|---|---|
| Software engineer CV | "Data Scientist" | Gaps in stats/ML, YT recs for those |
| Marketing CV | "Product Manager" | Gaps in analytics/specs, PM-specific recs |
| Empty/garbage PDF | any | Graceful error message |

**Day 6 local user test (via ngrok):**
1. `ngrok http 8000` → share link with 2–3 friends
2. Upload resume → get learning path within 30s
3. Click 1 YouTube link → verify it opens a real video
4. Capture: did they understand what to do? Did recs feel relevant? What broke?

---

## Pre-work needed from user (before Day 1 coding)

1. **Add OpenAI API credit** at platform.openai.com → create API key
2. **Create Google Cloud project** + enable YouTube Data API v3 + create API key — do this now, not on Day 4. Getting a GCP project approved (billing verification, API enablement) can take longer than expected and will block Day 4 if left until then. ~10 min, free quota.

---

## Risks + mitigations

| Risk | Mitigation |
|---|---|
| FastAPI + Jinja2 setup eats more than Day 1 | Have a pre-baked starter ready; if blocked, fall back to a single-file `app.py` for v1 |
| LLM hallucinating fake courses | Label clearly as "AI-suggested, verify"; YouTube data is real (API-backed) |
| LangGraph setup takes too long on Day 2 | Don't be precious about it — 4 plain `async` functions work just as well for a linear chain and are easier to debug |
| Scanned/image PDF fails silently | `pdf_loader.py` checks if extracted text is empty; shows fallback message instead of crashing |
| Bot or user drains OpenAI credits overnight | Rate limit: 1 analysis per IP per minute via `slowapi` or in-memory counter (Day 5) |
| YouTube API quota | Cache results per gap-skill in memory; 10K units/day is plenty for week 1 traffic |
| GCP approval delays YouTube integration | Do GCP setup in pre-work, not Day 4 |
| Scope creep ("just one more feature") | Strictly defer to phase 2 list; hosting decision comes only after local v1 is validated |

---

## Phase 2 (post-launch, week 2+)

- Google OAuth login
- Postgres (Render's free tier) — store resumes + learning paths per user
- Real Coursera/Udemy data (their affiliate APIs, not scraping)
- Review-based ranking + recency checks for YouTube videos
- Email follow-up with weekly check-ins
- Paid tier?
