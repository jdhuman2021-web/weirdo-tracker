"""
Database Migration Runner
Applies all migrations to Supabase in order

Usage: python database/run_migrations.py
"""

import sqlite3
from pathlib import Path
import sys
import os

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

MIGRATIONS_DIR = Path(__file__).parent / 'migrations'

def get_migration_files():
    """Get all migration files in order"""
    return sorted(MIGRATIONS_DIR.glob('*.sql'))

def run_migration(migration_file, conn):
    """Apply a single migration file"""
    print(f"Applying: {migration_file.name}")
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    try:
        cursor = conn.cursor()
        cursor.executescript(sql)
        conn.commit()
        print(f"  ✓ SUCCESS")
        return True
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        conn.rollback()
        return False

def check_migration_table(conn):
    """Create migration tracking table if not exists"""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

def is_migration_applied(conn, filename):
    """Check if migration was already applied"""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM _migrations WHERE filename = ?", (filename,))
    return cursor.fetchone() is not None

def record_migration(conn, filename):
    """Record successful migration"""
    conn.execute("INSERT INTO _migrations (filename) VALUES (?)", (filename,))
    conn.commit()

def main():
    print("Database Migration Runner")
    print("=" * 50)
    
    # Check migrations directory
    if not MIGRATIONS_DIR.exists():
        print("Creating migrations directory...")
        MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get migration files
    migrations = get_migration_files()
    
    if not migrations:
        print("No migration files found")
        return
    
    print(f"Found {len(migrations)} migration(s)")
    print()
    
    # Connect to SQLite
    db_path = Path(__file__).parent.parent / 'database' / 'tracker.db'
    conn = sqlite3.connect(db_path)
    
    # Ensure migration tracking table exists
    check_migration_table(conn)
    
    # Run migrations
    success_count = 0
    for migration_file in migrations:
        filename = migration_file.name
        
        # Skip if already applied
        if is_migration_applied(conn, filename):
            print(f"Skipping {filename} (already applied)")
            continue
        
        if run_migration(migration_file, conn):
            record_migration(conn, filename)
            success_count += 1
    
    conn.close()
    
    print()
    print("=" * 50)
    print(f"✓ Applied {success_count} new migration(s)")

if __name__ == "__main__":
    main()