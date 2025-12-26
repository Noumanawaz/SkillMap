import os
from functools import lru_cache
from pydantic import BaseModel


class Settings(BaseModel):
    ENV: str = os.getenv("ENV", "local")
    PROJECT_NAME: str = "SkillMap AI"

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://skillmap:skillmap@localhost:5432/skillmap_ai",
    )

    # Vector DB
    VECTOR_BACKEND: str = os.getenv("VECTOR_BACKEND", "memory")  # pinecone | weaviate | memory

    # AI / NLP
    HF_MODEL_NAME: str = os.getenv("HF_MODEL_NAME", "distilbert-base-uncased")
    SENTENCE_TRANSFORMER_MODEL: str = os.getenv(
        "SENTENCE_TRANSFORMER_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


