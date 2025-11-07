from typing import List, Tuple, Dict
import re
try:
    import spacy  # optional
    _NLP = spacy.load("en_core_web_sm")
except Exception:
    _NLP = None

SYNONYMS = {
    "js": "javascript",
    "reactjs": "react",
    "node.js": "node",
    "ts": "typescript",
    "sklearn": "scikit-learn",
    "tf": "tensorflow",
    "sql": "sql",
    "pyspark": "spark",
}


_SPLIT_RE = re.compile(r"\s*[;,/]|\]|\[|\(|\)\s*")


def normalize_skill(token: str) -> str:
    s = token.strip().lower()
    s = re.sub(r"[^a-z0-9+#.\- ]+", "", s)
    s = s.replace("structured query language", "sql")
    if s in SYNONYMS:
        s = SYNONYMS[s]
    return s


def parse_skills(raw: str) -> List[str]:
    if not raw:
        return []
    parts = [p for p in _SPLIT_RE.split(str(raw)) if p and p.strip()]
    norm = [normalize_skill(p) for p in parts]
    # dedupe preserving order
    seen = set()
    out = []
    for s in norm:
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def noun_chunk_skills(text: str) -> List[str]:
    if not _NLP:
        return []
    doc = _NLP(text[:10000])
    chunks = [c.text for c in doc.noun_chunks]
    return [normalize_skill(c) for c in chunks]


def extract_skills(text: str) -> List[str]:
    heuristic = re.findall(r"[A-Za-z][A-Za-z0-9+.#-]{1,}\b", text or "")
    base = [normalize_skill(t) for t in heuristic]
    if _NLP:
        base += noun_chunk_skills(text)
    # dedupe
    seen = set()
    out = []
    for s in base:
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out[:200]


def analyze_profile_text(text: str) -> Tuple[str, List[str]]:
    text = (text or "").strip()
    text = re.sub(r"[\x00-\x1F]+", " ", text)[:10000]
    skills = extract_skills(text)
    # naive summary: first 600 chars
    summary = text[:600]
    return summary, skills


