# AI-Driven Job Recommendation & Skill-Gap Analysis — Technical Documentation

## 1) Overview
This repository provides a production-ready prototype that ingests a candidate profile (paste text or upload PDF/DOCX/TXT, or pick a demo resume) and recommends relevant job roles with transparent scoring and a skill-gap analysis (present/missing/weak), including course suggestions and a 3‑month learning roadmap.

- Backend: FastAPI (Python 3.11), Pandas, scikit‑learn (TF‑IDF), Sentence-Transformers (SBERT), RapidFuzz, spaCy (optional), python‑docx, PyPDF2; SQLite for profile + embedding cache
- Frontend: Next.js 15 (App Router) + TypeScript + Tailwind; simple UI with recommendations list and Gap Drawer; Eval page for offline metrics
- Ops: Docker (api + web), Makefile targets, basic tests


## 2) Data model and assumptions
Input CSVs live in `data/`:
- `clean_jobs.csv` (required) with columns:
  - `job_id` (string; auto-generated if missing), `title`, `description`
  - `clean_skills` (preferred; else fallback to `skills`/`keywords`/`responsibilities`)
  - optional: `experience_level`, `years_experience`
- `clean_resume_data.csv` (optional demo) with columns like:
  - `resume_id`, `summary`/`fulltext`, `clean_skills`/`parsed_skills`, `education`, `courses`
- `skills_to_courses.csv` (optional mapping) with columns:
  - `skill`, `course_name`, `provider`, `hours`

Loader normalizes columns to snake_case, trims/`fillna`, deduplicates by `job_id`, and ensures a non-empty `job_id` for every row.


## 3) Backend (FastAPI) — key modules and responsibilities
- `app/main.py`
  - FastAPI app wiring with CORS and route registration
- `app/settings.py`
  - Configuration loader via env (DATA_DIR, MODEL_NAME, CACHE_DB, etc.)
- `app/routes/api.py` (REST API)
  - `GET /health` – liveness
  - `GET /schema/jobs` – detected job columns + sample
  - `POST /ingest/reload` – reload CSVs, rebuild caches
  - `GET /candidates` – demo resumes list if present
  - `POST /profile/analyze` – analyze pasted text or uploaded file; returns `{profile_id, summary, skills, persona}`
  - `GET /recommend/by_profile?profile_id=...&k=10&mode={baseline|embed|hybrid}`
  - `GET /recommend/by_resume_id?resume_id=...&k=10&mode=...`
  - `GET /gaps?profile_id=...&job_id=...` or `?resume_id=...&job_id=...`
  - `GET /eval/offline?mode=...&k=...` – synthetic metrics
- `app/services/loader.py`
  - Load/normalize jobs and resumes CSV, provide helpers to build `job_text = title + description + skills`
- `app/services/skills.py`
  - Skill parsing/normalization: lowercasing, punctuation strip, synonym mapping (js→javascript, reactjs→react, node.js→node, ts→typescript, sklearn→scikit‑learn, tf→tensorflow, sql, pyspark→spark)
  - Optional spaCy noun-chunk extraction
  - `analyze_profile_text(text)` → `(summary, skills)` with input sanitation (~10k char cap)
- `app/services/embeddings.py`
  - SBERT `all-MiniLM-L6-v2` model loader and SQLite cache (`.cache/embeddings.sqlite`)
  - Hashes text (sha256) to avoid duplicates; stores float32 vectors; returns normalized embeddings
- `app/services/recommender.py`
  - TF‑IDF baseline over `job_text`; cosine similarity
  - SBERT embedding similarity with cached job vectors
  - Skill overlap via Jaccard(resume_skills, job_skills)
  - Experience alignment heuristic (title vs persona)
  - Hybrid score with weights (persona-aware)
  - Formats top‑K with score breakdown and stable sorting; returns `job_id` and `jobId` for UI robustness
- `app/services/gaps.py`
  - Compute present/missing/weak skills for a profile or a resume-id
  - Map missing skills to courses (`skills_to_courses.csv` if present, else generic suggestions)
  - Generate 3‑month roadmap (foundations → intermediate → integration)
- `app/services/parse_file.py`
  - Extract text from PDF/DOCX/TXT with length limits
- `app/services/titles_ontology.py`
  - Canonicalizes titles with fuzzy matching (e.g., “software eng” → “software engineer”)
- `app/store.py`
  - Profiles SQLite (`.cache/profiles.sqlite`): `id`, `summary`, `skills`, `persona`
  - `skills_to_courses.csv` loader helper


## 4) API contracts (selected)
- `POST /profile/analyze`
  - Body: multipart (optional `file`) + fields `text?: string`, `persona?: string`
  - Returns `{ profile_id, summary, skills, persona }`
- `GET /recommend/by_profile`
  - Query: `profile_id`, `k`, `mode`
  - Returns `{ results: [{ job_id, title, experience_level, score, breakdown }] }`
- `GET /gaps`
  - Query: `profile_id` or `resume_id`, and `job_id`
  - Returns `{ present, missing, weak, suggestions: { skill: [{course_name,provider,hours}] }, roadmap_3mo }`


## 5) ML/NLP pipeline
### 5.1 Text construction
- Profile text: `summary/fulltext + normalized_skills + persona`
- Job text: `title + description + clean_skills`

### 5.2 Baseline keyword model
- scikit‑learn `TfidfVectorizer(max_features=50k, ngram_range=(1,2))`
- Cosine similarity of profile vector to job matrix

### 5.3 Semantic model (SBERT)
- Sentence-Transformers `all-MiniLM-L6-v2`
- Normalize embeddings (L2) and compute cosine via dot product
- Cache embeddings in SQLite keyed by text hash; batch encode on cache misses

### 5.4 Hybrid scoring and personas
- Components:
  - `embed_sim` (SBERT cosine)
  - `skill_overlap` (Jaccard of skill sets)
  - `exp_alignment` (heuristic from title vs persona; e.g., Fresh Grad prefers “junior”)
  - `keyword_overlap` (max of TF‑IDF cosine and RapidFuzz token_set_ratio/100)
- Default weights (persona-adjusted):
  - Hybrid: `0.55*embed + 0.25*skill + 0.15*exp + 0.05*kw`
  - Persona presets slightly tweak weights (Fresh Grad ↑exp; Switcher ↑skill; Retraining ↑skill/kw)
- Stable sort and tie-break on `job_id`

### 5.5 Skill-gap analysis
- Required skills from job row → normalized
- Present skills from profile/resume
- Gaps = `required - present`; “weak” = subset of present∩required (heuristic)
- Course suggestions via mapping CSV; else generic
- 3‑month plan: Month 1 foundations (top 2), Month 2 intermediate (next 2), Month 3 integration + interview prep


## 6) Frontend (Next.js, TypeScript, Tailwind)
- Pages (App Router):
  - `/` – Tabs: Paste Profile, Upload Resume, Pick from Dataset; Persona select; Analyze & Recommend button
  - `/candidate/[profileId]` – Mode toggle (baseline/embed/hybrid); job list; score breakdown; Gap Drawer with present/missing/weak, suggestions, roadmap
  - `/eval` – Offline metrics (Precision@K/Recall@K/NDCG@K) for each mode
- Data flow:
  - Paste/upload → `POST /profile/analyze` → redirect to `/candidate/[profileId]`
  - Dataset flow uses `resume_id` → recommendations via `/recommend/by_resume_id`
  - Gap Drawer calls `/gaps` with `profile_id` or `resume_id` + `job_id`
- UI libraries: plain Tailwind for layout; you can plug Recharts for radar/stacked bars later


## 7) Workflow (end-to-end)
1. User opens `/`
2. Chooses persona and provides profile text or uploads a file (or picks a demo resume)
3. Backend analyzes text → summary + skills; stores a `profile_id`
4. Recommendations page requests top‑K jobs using selected mode
5. User opens Gap Drawer for a specific job → backend returns present/missing/weak plus suggestions and roadmap
6. Optional: run `/eval` to compare models (synthetic offline metrics when no labels)


## 8) Storage and caching
- Profiles: `.cache/profiles.sqlite`
- Embeddings: `.cache/embeddings.sqlite` with table `embeddings(hash TEXT PRIMARY KEY, vec BLOB)`
- Data directory: configured via `DATA_DIR`; loader reload is available at `POST /ingest/reload`


## 9) Configuration
- `.env` (or environment variables):
  - `DATA_DIR=./data`
  - `MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2`
  - `CACHE_DB=.cache/embeddings.sqlite`
  - `CORS_ORIGINS=http://localhost:3000`
  - `DEFAULT_MODE=hybrid`


## 10) Running (Windows quickstart)
- Backend (Conda):
  - `conda create -n jobrec python=3.11 -y && conda activate jobrec`
  - `cd backend && pip install -r requirements.txt`
  - `python -m uvicorn app.main:app --reload --port 8000`
- Frontend:
  - `cd web && npm install && npm run dev -- --port 3000`
- Docker: `docker compose up --build`


## 11) Testing and quality
- Backend tests: `backend/tests/test_services.py` (loader, skills, recommender)
- Lint/format: Ruff/Black (`backend/pyproject.toml`), ESLint/Prettier on web
- Playwright stub in `web` with script `test:e2e` (can be expanded)


## 12) Extensibility
- Swap model: set `MODEL_NAME` to a different Sentence-Transformer
- Add skill ontology: extend `skills.py` synonyms and `titles_ontology.py`
- Enrich scores: incorporate company, location, salary; add reranking
- Collect feedback: extend `store.py` feedback table and add UI buttons wiring
- Charts: integrate Recharts radar/bar for coverage and score breakdown


## 13) Security & performance notes
- Input capped to ~10k chars; strip control chars; robust parsing of lists
- Embedding caching avoids repeated encoding; vectors stored as float32
- spaCy is optional and gracefully disabled if unavailable
- Stable sort and job_id normalization to prevent UI edge cases


