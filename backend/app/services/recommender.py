from typing import Dict, List
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import fuzz

from . import loader, skills as skills_svc, embeddings as emb
from ..settings import settings
from ..store import Store


_tfidf: TfidfVectorizer | None = None
_job_matrix = None
_job_index: List[str] = []
_job_texts: List[str] = []


def rebuild_caches():
    global _tfidf, _job_matrix, _job_index, _job_texts
    jobs_df, _ = loader.get_jobs()
    if jobs_df is None or len(jobs_df) == 0:
        _tfidf = None
        _job_matrix = None
        _job_index = []
        _job_texts = []
        return
    _job_texts = [loader.build_job_text(r) for _, r in jobs_df.iterrows()]
    _job_index = [str(r.get("job_id", i)) for i, r in jobs_df.iterrows()]
    _tfidf = TfidfVectorizer(max_features=50000, ngram_range=(1, 2))
    _job_matrix = _tfidf.fit_transform(_job_texts)
    # warm embedding cache
    emb.get_embeddings(_job_texts)


def _persona_weights(persona: str) -> Dict[str, float]:
    # base weights
    w = {"embed": 0.55, "skill": 0.25, "exp": 0.15, "kw": 0.05}
    p = (persona or "").lower()
    if "fresh" in p:
        w["exp"] = 0.2
        w["skill"] = 0.25
        w["embed"] = 0.5
    elif "switch" in p:
        w["skill"] = 0.3
        w["embed"] = 0.5
        w["exp"] = 0.15
    elif "retrain" in p:
        w["skill"] = 0.3
        w["embed"] = 0.5
        w["kw"] = 0.1
    return w


def _exp_alignment(job_title: str, persona: str) -> float:
    jt = (job_title or "").lower()
    if "senior" in jt or "lead" in jt:
        return 0.2 if "fresh" in persona.lower() else 0.5 if "switch" in persona.lower() else 0.6
    if "junior" in jt or "associate" in jt or "entry" in jt:
        return 1.0 if "fresh" in persona.lower() else 0.8
    return 0.7


def _get_resume_text_and_skills_by_resume_id(resume_id: str):
    resumes = loader.get_resumes_df()
    if resumes is None:
        return "", []
    row = resumes[resumes["resume_id"].astype(str) == str(resume_id)]
    if row.empty:
        return "", []
    r = row.iloc[0]
    text = str(r.get("summary", r.get("fulltext", "")))
    skills = []
    for col in ["clean_skills", "parsed_skills"]:
        if col in r and r[col]:
            skills += skills_svc.parse_skills(str(r[col]))
    if not skills:
        skills = skills_svc.extract_skills(text)
    return text, skills


def _profile_text(profile: Dict) -> str:
    skills = ", ".join(profile.get("skills", []))
    persona = profile.get("persona", "")
    return " \n".join([profile.get("summary", ""), skills, persona])


def _compute_components(profile_text: str, profile_skills: List[str]) -> Dict[str, np.ndarray]:
    global _tfidf, _job_matrix, _job_texts
    if _tfidf is None:
        rebuild_caches()
    components: Dict[str, np.ndarray] = {}
    if _tfidf is not None and _job_matrix is not None:
        v = _tfidf.transform([profile_text])
        components["tfidf"] = cosine_similarity(v, _job_matrix).ravel()
    # embeddings
    job_vecs = emb.get_embeddings(_job_texts) if _job_texts else np.zeros((0, 384))
    prof_vec = emb.get_embeddings([profile_text]) if profile_text else np.zeros((1, 384))
    if len(job_vecs) > 0:
        sim = (job_vecs @ prof_vec.T).ravel()
        components["embed"] = sim
    # skill overlap
    jobs_df, _ = loader.get_jobs()
    overlaps = []
    ps = set(profile_skills)
    for _, row in jobs_df.iterrows():
        js = set(skills_svc.parse_skills(row.get("clean_skills", "")))
        inter = len(ps & js)
        union = len(ps | js) if (ps or js) else 1
        overlaps.append(inter / union)
    components["skill"] = np.array(overlaps, dtype=float)
    # keyword fuzz
    kw = []
    for jt in _job_texts:
        kw.append(fuzz.token_set_ratio(profile_text, jt) / 100.0)
    components["kw"] = np.array(kw, dtype=float)
    return components


def _score_components(components: Dict[str, np.ndarray], jobs_df, persona: str) -> Dict[str, np.ndarray]:
    w = _persona_weights(persona)
    n = len(jobs_df)
    exp = np.array([_exp_alignment(jobs_df.iloc[i].get("title", ""), persona) for i in range(n)])
    embed_sim = components.get("embed", np.zeros(n))
    skill_overlap = components.get("skill", np.zeros(n))
    keyword_overlap = components.get("kw", np.zeros(n))
    # tfidf if present can be used as kw too
    if "tfidf" in components:
        keyword_overlap = np.maximum(keyword_overlap, components["tfidf"])  # take better of two
    final = w["embed"] * embed_sim + w["skill"] * skill_overlap + w["exp"] * exp + w["kw"] * keyword_overlap
    return {
        "final": final,
        "embed": embed_sim,
        "skill": skill_overlap,
        "exp": exp,
        "kw": keyword_overlap,
    }


def _format_results(scores: Dict[str, np.ndarray], jobs_df, k: int) -> List[Dict]:
    order = np.argsort(-scores["final"], kind="stable")[:k]
    out = []
    for idx in order:
        row = jobs_df.iloc[idx]
        jid = str(row.get("job_id", _job_index[idx] if idx < len(_job_index) else idx))
        out.append({
            "job_id": jid,
            "jobId": jid,
            "title": row.get("title", ""),
            "experience_level": row.get("experience_level", ""),
            "score": float(scores["final"][idx]),
            "breakdown": {
                "embed": float(scores["embed"][idx]),
                "skill": float(scores["skill"][idx]),
                "exp": float(scores["exp"][idx]),
                "kw": float(scores["kw"][idx]),
            },
        })
    return out


def recommend_for_profile(profile_id: str, k: int = 10, mode: str = None) -> List[Dict]:
    mode = mode or settings.default_mode
    profile = Store().get_profile(profile_id)
    if not profile:
        return []
    jobs_df, _ = loader.get_jobs()
    if jobs_df is None or len(jobs_df) == 0:
        return []
    text = _profile_text(profile)
    comps = _compute_components(text, profile.get("skills", []))
    # If a specific mode is requested, override weights
    if mode == "baseline":
        comps = {k: v for k, v in comps.items() if k in ("tfidf", "kw")}
    elif mode == "embed":
        comps = {k: v for k, v in comps.items() if k in ("embed",)}
    scores = _score_components(comps, jobs_df, profile.get("persona", settings.default_persona))
    return _format_results(scores, jobs_df, k)


def recommend_for_resume_id(resume_id: str, k: int = 10, mode: str = None) -> List[Dict]:
    mode = mode or settings.default_mode
    text, skills = _get_resume_text_and_skills_by_resume_id(resume_id)
    if not text:
        return []
    jobs_df, _ = loader.get_jobs()
    if jobs_df is None or len(jobs_df) == 0:
        return []
    comps = _compute_components(text, skills)
    if mode == "baseline":
        comps = {k: v for k, v in comps.items() if k in ("tfidf", "kw")}
    elif mode == "embed":
        comps = {k: v for k, v in comps.items() if k in ("embed",)}
    scores = _score_components(comps, jobs_df, settings.default_persona)
    return _format_results(scores, jobs_df, k)


def offline_eval(mode: str = None, k: int = 10) -> Dict[str, float]:
    # synthetic evaluation (no labels): compute diversity and self-consistency
    mode = mode or settings.default_mode
    jobs_df, _ = loader.get_jobs()
    resumes = loader.get_resumes_df()
    if jobs_df is None or resumes is None or len(resumes) == 0:
        return {"precision@k": 0.0, "recall@k": 0.0, "ndcg@k": 0.0}
    # Use profile built from each resume and compute average top-k similarity > threshold as proxy precision
    sims = []
    for _, r in resumes.head(20).iterrows():
        text = str(r.get("summary", r.get("fulltext", "")))
        skills = skills_svc.parse_skills(str(r.get("clean_skills", "")))
        comps = _compute_components(text, skills)
        if mode == "baseline":
            comps = {k: v for k, v in comps.items() if k in ("tfidf", "kw")}
        elif mode == "embed":
            comps = {k: v for k, v in comps.items() if k in ("embed",)}
        scores = _score_components(comps, jobs_df, settings.default_persona)
        topk = np.sort(scores["final"])[-k:]
        sims.append(float(np.mean(topk)))
    avg = float(np.mean(sims)) if sims else 0.0
    return {"precision@k": avg, "recall@k": avg, "ndcg@k": avg}


