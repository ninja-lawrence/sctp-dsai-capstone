import os
import json
from typing import Dict, Tuple, Optional
import pandas as pd
from ..settings import settings


_jobs_df: Optional[pd.DataFrame] = None
_resumes_df: Optional[pd.DataFrame] = None
_meta: Dict = {}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df


def _load_jobs() -> Tuple[Optional[pd.DataFrame], Dict]:
    path = os.path.join(settings.data_dir, "clean_jobs.csv")
    if not os.path.exists(path):
        return None, {"found": False}
    df = pd.read_csv(path)
    df = _normalize_columns(df)
    expected = ["title", "description"]
    for col in expected:
        if col not in df.columns:
            df[col] = ""
    # ensure job_id exists and is non-empty
    if "job_id" not in df.columns:
        df["job_id"] = [str(i + 1) for i in range(len(df))]
    else:
        df["job_id"] = df["job_id"].astype(str)
        df.loc[df["job_id"].isin(["", "nan", "None"]), "job_id"] = [str(i + 1) for i in range(len(df))]
    # skills field normalization with fallbacks
    skill_cols = ["clean_skills", "skills", "keywords", "responsibilities"]
    chosen = None
    for c in skill_cols:
        if c in df.columns:
            chosen = c
            break
    if chosen is None:
        df["clean_skills"] = ""
    elif chosen != "clean_skills":
        df["clean_skills"] = df[chosen].fillna("")
    df = df.fillna("").drop_duplicates(subset=["job_id"]) if "job_id" in df.columns else df.drop_duplicates()
    return df, {"found": True, "rows": len(df)}


def _load_resumes() -> Tuple[Optional[pd.DataFrame], Dict]:
    path = os.path.join(settings.data_dir, "clean_resume_data.csv")
    if not os.path.exists(path):
        return None, {"found": False}
    df = pd.read_csv(path)
    df = _normalize_columns(df)
    if "resume_id" not in df.columns:
        df["resume_id"] = range(1, len(df) + 1)
    return df.fillna("") , {"found": True, "rows": len(df)}


def reload_all():
    global _jobs_df, _resumes_df, _meta
    _jobs_df, jobs_meta = _load_jobs()
    _resumes_df, resumes_meta = _load_resumes()
    _meta = {"jobs": jobs_meta, "resumes": resumes_meta}


def get_jobs() -> Tuple[Optional[pd.DataFrame], Dict]:
    if _jobs_df is None:
        reload_all()
    return _jobs_df, _meta.get("jobs", {})


def get_resumes_df() -> Optional[pd.DataFrame]:
    if _resumes_df is None:
        reload_all()
    return _resumes_df


def build_job_text(row: pd.Series) -> str:
    skills = str(row.get("clean_skills", ""))
    title = str(row.get("title", ""))
    desc = str(row.get("description", ""))
    return " \n".join([title, desc, skills])


