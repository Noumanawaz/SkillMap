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
    
    # Gemini
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.0-flash"

    
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
    
    # Demo Mode
    demo_mode: bool = False
    demo_user_email: Optional[str] = None  # If set, this user gets demo responses
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Also check environment variables directly as fallback (for Coolify/Docker deployments)
        if not self.gemini_api_key:
            self.gemini_api_key = os.getenv("GEMINI_API_KEY")
            if self.gemini_api_key:
                print(f"✅ GEMINI_API_KEY loaded from environment variable")
            else:
                print(f"⚠️  GEMINI_API_KEY not found in environment variables")
                # Debug: show what env vars are available (without exposing values)
                gemini_vars = [k for k in os.environ.keys() if 'GEMINI' in k.upper() or 'AI' in k.upper()]
                if gemini_vars:
                    print(f"   Found related env vars: {', '.join(gemini_vars)}")
                else:
                    print(f"   No Gemini-related environment variables found")
        
        # Check for demo mode
        if not self.demo_mode:
            demo_mode_env = os.getenv("DEMO_MODE", "false").lower()
            self.demo_mode = demo_mode_env == "true"
        if not self.demo_user_email:
            self.demo_user_email = os.getenv("DEMO_USER_EMAIL")
        
        if self.demo_mode:
            if self.demo_user_email:
                print(f"🎬 DEMO MODE enabled for user: {self.demo_user_email}")
            else:
                print(f"🎬 DEMO MODE enabled for all users")


# Don't cache settings to ensure .env changes are picked up
def get_settings() -> Settings:
    return Settings()

