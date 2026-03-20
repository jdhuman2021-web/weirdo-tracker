"""
Migrate existing JSON data to SQLite database
Imports tokens.json and opportunities.json into the database
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
import sys

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = Path(__file__).parent / "tracker.db"
TOKENS_JSON = Path(__file__).parent.parent / "config" / "tokens.json"
OPPORTUNITIES_JSON = Path(__file__).parent.parent / "data" / "opportunities.json"

def migrate_tokens():
    """Import tokens from config/tokens.json"""
    
    if not TOKENS_JSON.exists():
        print("WARN: tokens.json not found, skipping...")
        return 0
    
    with open(TOKENS_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    tokens = data.get('tokens', [])
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    imported = 0
    for token in tokens:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO tokens 
                (symbol, name, address, chain, added_date, source, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                token.get('symbol'),
                token.get('name'),
                token.get('address'),
                token.get('chain', 'SOL'),
                token.get('added_date'),
                token.get('source'),
                token.get('notes', '')
            ))
            imported += 1
        except Exception as e:
            print(f"Error importing {token.get('symbol')}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"Imported {imported} tokens")
    return imported

def migrate_opportunities():
    """Import latest opportunities as price snapshots"""
    
    if not OPPORTUNITIES_JSON.exists():
        print("WARN: opportunities.json not found, skipping...")
        return 0
    
    with open(OPPORTUNITIES_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    opportunities = data.get('opportunities', [])
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    imported = 0
    for opp in opportunities:
        try:
            cursor.execute("""
                INSERT INTO price_snapshots 
                (token_address, price_usd, market_cap, volume_24h, liquidity_usd,
                 price_change_1h, price_change_24h, holder_count, age_hours, score, signal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                opp.get('address'),
                opp.get('price_usd'),
                opp.get('market_cap'),
                opp.get('volume_24h'),
                opp.get('liquidity_usd'),
                opp.get('price_change_1h'),
                opp.get('price_change_24h'),
                opp.get('holder_count', 0),
                opp.get('age_hours'),
                opp.get('score'),
                opp.get('signal')
            ))
            imported += 1
        except Exception as e:
            print(f"Error importing {opp.get('symbol')}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"Imported {imported} price snapshots")
    return imported

def main():
    """Run full migration"""
    print("Migrating JSON data to SQLite...")
    print("=" * 50)
    
    token_count = migrate_tokens()
    snapshot_count = migrate_opportunities()
    
    print("=" * 50)
    print(f"Migration complete!")
    print(f"   Tokens: {token_count}")
    print(f"   Snapshots: {snapshot_count}")

if __name__ == "__main__":
    main()
