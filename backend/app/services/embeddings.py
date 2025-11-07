import hashlib
import os
import sqlite3
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

from ..settings import settings


_MODEL: SentenceTransformer | None = None


def _ensure_db():
    os.makedirs(os.path.dirname(settings.cache_db), exist_ok=True)
    with sqlite3.connect(settings.cache_db) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS embeddings (hash TEXT PRIMARY KEY, vec BLOB)"
        )


def _get_model() -> SentenceTransformer:
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer(settings.model_name)
    return _MODEL


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_embeddings(texts: List[str]) -> np.ndarray:
    _ensure_db()
    model = _get_model()
    hashes = [_hash_text(t) for t in texts]
    vecs: List[np.ndarray] = [None] * len(texts)  # type: ignore
    missing_idxs = []
    with sqlite3.connect(settings.cache_db) as conn:
        for i, h in enumerate(hashes):
            cur = conn.execute("SELECT vec FROM embeddings WHERE hash=?", (h,))
            row = cur.fetchone()
            if row is not None:
                vecs[i] = np.frombuffer(row[0], dtype=np.float32)
            else:
                missing_idxs.append(i)
        if missing_idxs:
            to_encode = [texts[i] for i in missing_idxs]
            enc = model.encode(to_encode, convert_to_numpy=True, normalize_embeddings=True)
            for j, i in enumerate(missing_idxs):
                v = enc[j].astype(np.float32)
                vecs[i] = v
                conn.execute("INSERT OR REPLACE INTO embeddings(hash, vec) VALUES (?, ?)", (hashes[i], v.tobytes()))
            conn.commit()
    return np.vstack(vecs)


