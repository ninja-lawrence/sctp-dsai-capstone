from rapidfuzz import fuzz

CANONICAL = {
    "software engineer": ["software eng", "swe", "software developer", "developer"],
    "data scientist": ["ds", "ml scientist"],
    "data engineer": ["de", "etl engineer"],
    "ml engineer": ["machine learning engineer", "ml eng"],
}


def canonicalize(title: str, threshold: int = 85) -> str:
    t = (title or "").lower()
    for canon, variants in CANONICAL.items():
        if fuzz.partial_ratio(t, canon) >= threshold:
            return canon
        for v in variants:
            if fuzz.partial_ratio(t, v) >= threshold:
                return canon
    return t


