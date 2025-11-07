import os
import pandas as pd
from app.services import loader, skills, recommender


def test_loader_jobs(tmp_path, monkeypatch):
    p = tmp_path / "data"
    p.mkdir()
    (p / "clean_jobs.csv").write_text("job_id,title,description,clean_skills\n1,SE,Build stuff,python;sql\n")
    monkeypatch.setenv("DATA_DIR", str(p))
    from importlib import reload
    from app import settings as settings_mod
    reload(settings_mod)
    reload(loader)
    df, meta = loader.get_jobs()
    assert df is not None and len(df) == 1
    assert meta["found"]


def test_skills_parsing():
    parsed = skills.parse_skills("js; reactjs, node.js / TS")
    assert "javascript" in parsed and "react" in parsed and "node" in parsed and "typescript" in parsed


def test_recommender_scoring(monkeypatch, tmp_path):
    p = tmp_path / "data"
    p.mkdir()
    (p / "clean_jobs.csv").write_text("job_id,title,description,clean_skills\n1,Data Scientist,ML work,python;ml\n2,Software Engineer,Web work,javascript;react\n")
    monkeypatch.setenv("DATA_DIR", str(p))
    from importlib import reload
    from app import settings as settings_mod
    reload(settings_mod)
    from app.services import loader as l2
    reload(l2)
    recommender.rebuild_caches()
    # simple profile
    text = "I know python and ml projects"
    comps = recommender._compute_components(text, ["python","ml"])  # type: ignore
    assert "embed" in comps and "skill" in comps


