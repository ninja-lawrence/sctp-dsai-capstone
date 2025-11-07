# AI-Driven Job Recommendation & Skill-Gap Analysis (Prototype)

## Quickstart

- Prereqs: Python 3.11, Node 18+, Docker (optional)
- Data: place CSVs in `data/`:
  - `clean_jobs.csv` (required)
  - `clean_resume_data.csv` (optional demo)
  - `skills_to_courses.csv` (optional mapping)

### Dev

- Local: `make dev` (starts FastAPI on :8000 and Next.js on :3000)
- Docker: `make up` / `make down`

API base: `http://localhost:8000`
Web: `http://localhost:3000`

## .env

- DATA_DIR=./data
- MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
- CACHE_DB=.cache/embeddings.sqlite
- CORS_ORIGINS=http://localhost:3000
- DEFAULT_MODE=hybrid

## Acceptance criteria

- Paste/upload resume → analyze → job recommendations
- Gap drawer shows present/missing/weak + courses + roadmap
- Eval page compares baseline vs embedding vs hybrid

_Screenshots TBD_

## Windows setup (PowerShell)

### Option A: Conda (recommended)

```powershell
# 1) Backend (FastAPI)
cd C:\Users\genda\Downloads\sctp\capstone\project

conda create -n jobrec python=3.11 -y
conda activate jobrec

cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm  # optional; ok if it fails

# env and run
mkdir ..\.cache -ea 0
$env:DATA_DIR="..\data"
$env:MODEL_NAME="sentence-transformers/all-MiniLM-L6-v2"
$env:CACHE_DB="..\.cache\embeddings.sqlite"
$env:CORS_ORIGINS="http://localhost:3000"
$env:DEFAULT_MODE="hybrid"

python -m uvicorn app.main:app --reload --port 8000
```

```powershell
# 2) Frontend (Next.js) — new PowerShell window
cd C:\Users\genda\Downloads\sctp\capstone\project\web
npm install
$env:NEXT_PUBLIC_API_BASE="http://localhost:8000"
npm run dev -- --port 3000
```

### Option B: venv (built-in Python)

```powershell
cd C:\Users\genda\Downloads\sctp\capstone\project\backend
py -3.11 -m venv .venv
.; .\.venv\Scripts\Activate.ps1
py -3.11 -m pip install -r requirements.txt
py -3.11 -m spacy download en_core_web_sm  # optional
mkdir ..\.cache -ea 0
$env:DATA_DIR="..\data"
py -3.11 -m uvicorn app.main:app --reload --port 8000
```

Frontend commands are the same as above.

### Option C: Docker

```powershell
cd C:\Users\genda\Downloads\sctp\capstone\project
docker compose up --build
```

API: `http://localhost:8000` · Web: `http://localhost:3000`

### Common issues

- make not found: Windows doesn’t ship `make`. Use the commands above instead of `make dev`.
- uvicorn not found: run via `python -m uvicorn ...` (ensures the current env’s uvicorn).
- Form upload error (python-multipart): `pip install python-multipart` (already in `requirements.txt`).
- Next.js CSS error “Cannot find module 'autoprefixer'”: run in `web/` → `npm install` (we include `postcss` and `autoprefixer`). If it persists, delete `.next`, `node_modules`, and `package-lock.json`, then `npm install`.
- Empty recommendations: ensure `data/clean_jobs.csv` exists and `DATA_DIR` points to your `data` folder. Check `http://localhost:8000/schema/jobs` shows rows > 0. You can force reload with `POST /ingest/reload`.
- “View Gaps” shows nothing: ensure each recommendation has a non-empty `job_id`. The loader auto-generates IDs if missing.


