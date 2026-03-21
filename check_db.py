import sqlite3

conn = sqlite3.connect('database/tracker.db')
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print('TABLES:', tables)
print()

# Check tokens count
cursor.execute('SELECT COUNT(*) FROM tokens')
token_count = cursor.fetchone()[0]
print('TOKENS IN DB:', token_count)

# Check price snapshots count
cursor.execute('SELECT COUNT(*) FROM price_snapshots')
snapshot_count = cursor.fetchone()[0]
print('SNAPSHOTS:', snapshot_count)

# Check latest snapshot
cursor.execute('SELECT captured_at FROM price_snapshots ORDER BY captured_at DESC LIMIT 1')
latest = cursor.fetchone()
print('LATEST SNAPSHOT:', latest[0] if latest else 'None')

conn.close()