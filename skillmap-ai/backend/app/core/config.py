from functools import lru_cache
from typing import List, Optional
import os
from pathlib import Path

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file explicitly before creating Settings
# This ensures the environment variables are available
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    # Try current directory
    load_dotenv()


class Settings(BaseSettings):
    # Database (supports PostgreSQL or SQLite)
    database_url: str = "sqlite:///./skillmap.db"  # Default to SQLite for easy setup
    
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 2000
    
    # Vector DB
    vector_db_backend: str = "in_memory"  # in_memory, pinecone, weaviate
    pinecone_api_key: Optional[str] = None
    pinecone_environment: Optional[str] = None
    weaviate_url: Optional[str] = None
    
    # Sentence Transformers
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # API
    api_v1_prefix: str = "/v1"
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Also check environment variables directly as fallback (for Coolify/Docker deployments)
        if not self.openai_api_key:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
            if self.openai_api_key:
                print(f"✅ OPENAI_API_KEY loaded from environment variable")
            else:
                print(f"⚠️  OPENAI_API_KEY not found in environment variables")
                # Debug: show what env vars are available (without exposing values)
                openai_vars = [k for k in os.environ.keys() if 'OPENAI' in k.upper() or 'AI' in k.upper()]
                if openai_vars:
                    print(f"   Found related env vars: {', '.join(openai_vars)}")
                else:
                    print(f"   No OpenAI-related environment variables found")


# Don't cache settings to ensure .env changes are picked up
def get_settings() -> Settings:
    return Settings()

