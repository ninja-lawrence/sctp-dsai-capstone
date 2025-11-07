from typing import Dict, List
from . import loader, skills as skills_svc
from . import recommender as rec
from ..store import Store


def _map_to_courses(skill: str) -> List[Dict]:
    # Try mapping CSV if present
    mapping_df = Store().get_skills_mapping()
    out: List[Dict] = []
    if mapping_df is not None:
        rows = mapping_df[mapping_df["skill"].str.lower() == skill.lower()]
        for _, r in rows.head(2).iterrows():
            out.append({
                "course_name": r.get("course_name", ""),
                "provider": r.get("provider", ""),
                "hours": r.get("hours", ""),
            })
    if not out:
        out = [
            {"course_name": f"Intro to {skill}", "provider": "Generic", "hours": "10-15"},
        ]
    return out


def _roadmap(skills: List[str]) -> str:
    s = skills[:4]
    m1 = ", ".join(s[:2]) or "foundations"
    m2 = ", ".join(s[2:4]) or "intermediate topics"
    cap = (s[0] if s else "your stack")
    return (
        f"Month 1: Foundations in {m1} + 1 mini-project\n"
        f"Month 2: Intermediate {m2} + an applied project\n"
        f"Month 3: Integration capstone in {cap} + mock interviews"
    )


def compute_gaps(profile_id: str, job_id: str) -> Dict:
    profile = Store().get_profile(profile_id)
    jobs_df, _ = loader.get_jobs()
    if not profile or jobs_df is None:
        return {"present": [], "missing": [], "weak": [], "suggestions": {}, "roadmap_3mo": ""}
    row = jobs_df[jobs_df["job_id"].astype(str) == str(job_id)]
    if row.empty:
        return {"present": [], "missing": [], "weak": [], "suggestions": {}, "roadmap_3mo": ""}
    job = row.iloc[0]
    job_skills = set(skills_svc.parse_skills(job.get("clean_skills", "")))
    present = set(profile.get("skills", []))
    missing = sorted(list(job_skills - present))
    weak = sorted(list(job_skills & present))[:3]  # heuristic: first few as weak
    suggestions = {s: _map_to_courses(s) for s in missing[:6]}
    roadmap = _roadmap(missing)
    return {
        "present": sorted(list(present)),
        "missing": missing,
        "weak": weak,
        "suggestions": suggestions,
        "roadmap_3mo": roadmap,
    }


def compute_gaps_for_resume(resume_id: str, job_id: str) -> Dict:
    text, skills = rec._get_resume_text_and_skills_by_resume_id(resume_id)  # type: ignore
    jobs_df, _ = loader.get_jobs()
    if not skills or jobs_df is None:
        return {"present": [], "missing": [], "weak": [], "suggestions": {}, "roadmap_3mo": ""}
    row = jobs_df[jobs_df["job_id"].astype(str) == str(job_id)]
    if row.empty:
        return {"present": [], "missing": [], "weak": [], "suggestions": {}, "roadmap_3mo": ""}
    job = row.iloc[0]
    job_skills = set(skills_svc.parse_skills(job.get("clean_skills", "")))
    present = set(skills)
    missing = sorted(list(job_skills - present))
    weak = sorted(list(job_skills & present))[:3]
    suggestions = {s: _map_to_courses(s) for s in missing[:6]}
    roadmap = _roadmap(missing)
    return {
        "present": sorted(list(present)),
        "missing": missing,
        "weak": weak,
        "suggestions": suggestions,
        "roadmap_3mo": roadmap,
    }


