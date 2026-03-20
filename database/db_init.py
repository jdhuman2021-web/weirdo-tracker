"""
Database Initialization Script
Creates SQLite database from schema.sql
"""

import sqlite3
from pathlib import Path
import sys

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def init_database(db_path: str = "tracker.db"):
    """Initialize database from schema.sql"""
    
    # Resolve paths relative to this script's directory
    script_dir = Path(__file__).parent
    db_file = script_dir / db_path
    schema_file = script_dir / "schema.sql"
    
    if not schema_file.exists():
        print(f"ERROR: schema.sql not found at {schema_file.absolute()}!")
        return False
    
    # Connect (creates file if doesn't exist)
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Read and execute schema
    with open(schema_file, 'r') as f:
        schema = f.read()
    
    cursor.executescript(schema)
    conn.commit()
    
    # Verify tables created
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"SUCCESS: Database initialized: {db_file.absolute()}")
    print(f"Tables created: {', '.join(tables)}")
    
    conn.close()
    return True

if __name__ == "__main__":
    init_database()
