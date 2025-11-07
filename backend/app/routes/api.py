from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
from ..settings import settings
from ..services import loader, skills as skills_svc, recommender, gaps as gaps_svc, parse_file
from ..store import Store

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/schema/jobs")
def schema_jobs():
    df, meta = loader.get_jobs()
    sample = df.head(3).to_dict(orient="records") if df is not None else []
    return {"columns": list(df.columns) if df is not None else [], "sample": sample, "meta": meta}


@router.post("/ingest/reload")
def ingest_reload():
    loader.reload_all()
    recommender.rebuild_caches()
    return {"status": "reloaded"}


@router.get("/candidates")
def candidates():
    resumes = loader.get_resumes_df()
    if resumes is None:
        return {"candidates": []}
    records = resumes[["resume_id", "summary"]].fillna("").to_dict(orient="records")
    return {"candidates": records}


@router.post("/profile/analyze")
async def profile_analyze(
    text: Optional[str] = Form(default=None),
    persona: Optional[str] = Form(default=None),
    file: Optional[UploadFile] = File(default=None),
):
    if not text and not file:
        raise HTTPException(status_code=400, detail="Provide text or upload a file")
    if file:
        content = await file.read()
        text = parse_file.extract_text(file.filename, content)
    summary, extracted_skills = skills_svc.analyze_profile_text(text)
    profile_id = Store().save_profile(summary, extracted_skills, persona or settings.default_persona)
    return {"profile_id": profile_id, "summary": summary, "skills": extracted_skills, "persona": persona or settings.default_persona}


@router.get("/recommend/by_profile")
def recommend_by_profile(profile_id: str, k: int = 10, mode: str = None):
    mode = mode or settings.default_mode
    results = recommender.recommend_for_profile(profile_id, k=k, mode=mode)
    return {"results": results}


@router.get("/recommend/by_resume_id")
def recommend_by_resume_id(resume_id: str, k: int = 10, mode: str = None):
    mode = mode or settings.default_mode
    results = recommender.recommend_for_resume_id(resume_id, k=k, mode=mode)
    return {"results": results}


@router.get("/gaps")
def gaps(profile_id: str | None = None, resume_id: str | None = None, job_id: str = ""):
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required")
    if profile_id:
        return gaps_svc.compute_gaps(profile_id, job_id)
    if resume_id:
        return gaps_svc.compute_gaps_for_resume(resume_id, job_id)
    raise HTTPException(status_code=400, detail="Provide profile_id or resume_id")


@router.get("/eval/offline")
def eval_offline(mode: str = None, k: int = 10):
    mode = mode or settings.default_mode
    return recommender.offline_eval(mode=mode, k=k)


