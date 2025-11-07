import os
from typing import List


class Settings:
    data_dir: str = os.getenv("DATA_DIR", "./data")
    model_name: str = os.getenv("MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
    cache_db: str = os.getenv("CACHE_DB", ".cache/embeddings.sqlite")
    cors_origins: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    default_mode: str = os.getenv("DEFAULT_MODE", "hybrid")
    default_persona: str = os.getenv("DEFAULT_PERSONA", "Fresh Grad")


settings = Settings()


