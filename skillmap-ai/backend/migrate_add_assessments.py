"""
Migration script to add skill_assessment table.
Run this once to update existing databases.
"""
import sqlite3
import sys
from pathlib import Path

# Get database path
db_path = Path(__file__).parent / "skillmap.db"

if not db_path.exists():
    print(f"Database not found at {db_path}")
    print("The skill_assessment table will be created automatically when you run the app.")
    sys.exit(0)

try:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check if table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='skill_assessment'")
    if cursor.fetchone():
        print("✅ skill_assessment table already exists")
    else:
        # Create skill_assessment table
        cursor.execute("""
            CREATE TABLE skill_assessment (
                assessment_id TEXT PRIMARY KEY,
                employee_id TEXT NOT NULL,
                skill_id TEXT NOT NULL,
                questions TEXT NOT NULL,
                answers TEXT,
                correct_answers TEXT,
                score REAL,
                difficulty_level REAL,
                readiness_score REAL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employee_profile(employee_id),
                FOREIGN KEY (skill_id) REFERENCES skill(skill_id)
            )
        """)
        conn.commit()
        print("✅ Successfully created skill_assessment table")
    
    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nNote: If using PostgreSQL, run this SQL manually:")
    print("""
CREATE TABLE IF NOT EXISTS skill_assessment (
    assessment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employee_profile(employee_id),
    skill_id UUID NOT NULL REFERENCES skill(skill_id),
    questions JSONB NOT NULL,
    answers JSONB,
    correct_answers JSONB,
    score REAL,
    difficulty_level REAL,
    readiness_score REAL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
    """)
    sys.exit(1)

