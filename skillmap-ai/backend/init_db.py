"""
Initialize the database by creating all tables.
This script should be run on startup to ensure the database exists.
"""
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import engine
from app.db.models import Base
from app.core.config import get_settings

def init_database():
    """Initialize the database by creating all tables."""
    settings = get_settings()
    
    # For SQLite, ensure the directory exists
    if settings.database_url.startswith("sqlite"):
        # Extract the database path from the URL
        # sqlite:///./data/skillmap.db -> ./data/skillmap.db
        db_path_str = settings.database_url.replace("sqlite:///", "").replace("sqlite://", "")
        if db_path_str and not db_path_str.startswith(":memory:"):
            # Get the app directory (where the script runs from)
            app_dir = Path(__file__).parent
            # Resolve the path relative to app directory
            db_file = (app_dir / db_path_str).resolve()
            # Ensure the parent directory exists
            db_file.parent.mkdir(parents=True, exist_ok=True)
            print(f"✅ Database directory ensured: {db_file.parent}")
            print(f"📁 Database file will be at: {db_file}")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)

