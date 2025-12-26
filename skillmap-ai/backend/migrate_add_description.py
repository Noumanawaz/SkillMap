"""
Migration script to add description column to employee_profile table.
Run this once to update existing databases.
"""
import sqlite3
import sys
from pathlib import Path

# Get database path
db_path = Path(__file__).parent / "skillmap.db"

if not db_path.exists():
    print(f"Database not found at {db_path}")
    print("The description column will be added automatically when you create the first employee.")
    sys.exit(0)

try:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(employee_profile)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "description" in columns:
        print("✅ Description column already exists in employee_profile table")
    else:
        # Add description column
        cursor.execute("ALTER TABLE employee_profile ADD COLUMN description TEXT")
        conn.commit()
        print("✅ Successfully added description column to employee_profile table")
    
    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nNote: If using PostgreSQL, run this SQL manually:")
    print("ALTER TABLE employee_profile ADD COLUMN IF NOT EXISTS description TEXT;")
    sys.exit(1)

