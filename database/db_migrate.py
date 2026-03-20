"""
Database Migration Runner
Applies SQL migrations to the database

Usage: python db_migrate.py
"""

import sqlite3
from pathlib import Path
import sys

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = Path(__file__).parent.parent / "database" / "tracker.db"
MIGRATIONS_DIR = Path(__file__).parent.parent / "database" / "migrations"

def run_migration(migration_file):
    """Apply a single migration file"""
    print(f"Applying: {migration_file.name}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    try:
        cursor.executescript(sql)
        conn.commit()
        print(f"  SUCCESS")
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """Run all pending migrations"""
    print("Database Migration Runner")
    print("=" * 50)
    
    if not MIGRATIONS_DIR.exists():
        print("No migrations folder found")
        return
    
    migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))
    
    if not migrations:
        print("No migration files found")
        return
    
    print(f"Found {len(migrations)} migration(s)")
    print()
    
    success = 0
    for migration in migrations:
        if run_migration(migration):
            success += 1
    
    print()
    print("=" * 50)
    print(f"Migrations complete: {success}/{len(migrations)} succeeded")

if __name__ == "__main__":
    main()
