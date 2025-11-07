import os
import json
import sqlite3
from typing import Dict, List, Optional
import pandas as pd

from .settings import settings


class Store:
    def __init__(self):
        os.makedirs(".cache", exist_ok=True)
        self._db_path = os.path.join(".cache", "profiles.sqlite")
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS profiles (id TEXT PRIMARY KEY, summary TEXT, skills TEXT, persona TEXT)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS feedback (profile_id TEXT, job_id TEXT, label INTEGER, ts DATETIME DEFAULT CURRENT_TIMESTAMP)"
            )

    def save_profile(self, summary: str, skills: List[str], persona: str) -> str:
        pid = str(abs(hash(summary + persona)))[0:16]
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO profiles(id, summary, skills, persona) VALUES (?, ?, ?, ?)",
                (pid, summary, json.dumps(skills), persona),
            )
            conn.commit()
        return pid

    def get_profile(self, profile_id: str) -> Optional[Dict]:
        with sqlite3.connect(self._db_path) as conn:
            cur = conn.execute("SELECT summary, skills, persona FROM profiles WHERE id=?", (profile_id,))
            row = cur.fetchone()
            if not row:
                return None
            return {"summary": row[0], "skills": json.loads(row[1] or "[]"), "persona": row[2]}

    def get_skills_mapping(self) -> Optional[pd.DataFrame]:
        path = os.path.join(settings.data_dir, "skills_to_courses.csv")
        if os.path.exists(path):
            df = pd.read_csv(path)
            df.columns = [c.strip().lower() for c in df.columns]
            if "skill" not in df.columns:
                return None
            return df.fillna("")
        return None


