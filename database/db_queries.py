"""
Database Query Utilities
Common functions for interacting with the tracker database
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "tracker.db"

def get_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ============ TOKENS ============

def add_token(symbol: str, name: str, address: str, chain: str = "SOL", 
              added_date: str = None, source: str = None, notes: str = ""):
    """Add a new token to the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO tokens (symbol, name, address, chain, added_date, source, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (symbol, name, address, chain, added_date or datetime.now().isoformat(), 
              source, notes))
        conn.commit()
        token_id = cursor.lastrowid
        print(f"✅ Added token: {symbol} (ID: {token_id})")
        return token_id
    except sqlite3.IntegrityError:
        print(f"⚠️ Token exists: {address}")
        return None
    finally:
        conn.close()

def get_all_tokens():
    """Get all tokens from database"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tokens ORDER BY symbol")
    tokens = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tokens

# ============ PRICE SNAPSHOTS ============

def add_price_snapshot(token_address: str, price_usd: float, market_cap: float,
                       volume_24h: float, liquidity_usd: float,
                       price_change_1h: float, price_change_24h: float,
                       holder_count: int, age_hours: int, 
                       score: int, signal: str):
    """Record a price snapshot for a token"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO price_snapshots 
        (token_address, price_usd, market_cap, volume_24h, liquidity_usd,
         price_change_1h, price_change_24h, holder_count, age_hours, score, signal)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (token_address, price_usd, market_cap, volume_24h, liquidity_usd,
          price_change_1h, price_change_24h, holder_count, age_hours, score, signal))
    
    conn.commit()
    snapshot_id = cursor.lastrowid
    conn.close()
    
    return snapshot_id

def get_latest_prices(limit: int = 50):
    """Get latest price snapshots using the view"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM latest_prices ORDER BY captured_at DESC LIMIT ?", (limit,))
    prices = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return prices

def get_price_history(token_address: str, hours: int = 24):
    """Get price history for a specific token"""
    conn = get_connection()
    cursor = conn.cursor()
    cutoff = datetime.now() - timedelta(hours=hours)
    cursor.execute("""
        SELECT * FROM price_snapshots 
        WHERE token_address = ? AND captured_at > ?
        ORDER BY captured_at DESC
    """, (token_address, cutoff.isoformat()))
    history = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return history

# ============ WHALE ACTIVITY ============

def add_whale_activity(token_address: str, whale_address: str, 
                       whale_name: str, action: str, 
                       amount_usd: float, tx_hash: str = None):
    """Record whale activity"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO whale_activity 
        (token_address, whale_address, whale_name, action, amount_usd, tx_hash)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (token_address, whale_address, whale_name, action, amount_usd, tx_hash))
    
    conn.commit()
    activity_id = cursor.lastrowid
    conn.close()
    
    return activity_id

def get_whale_activity(hours: int = 24):
    """Get recent whale activity"""
    conn = get_connection()
    cursor = conn.cursor()
    cutoff = datetime.now() - timedelta(hours=hours)
    cursor.execute("""
        SELECT * FROM whale_activity 
        WHERE captured_at > ?
        ORDER BY captured_at DESC
    """, (cutoff.isoformat(),))
    activity = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return activity

# ============ ALERTS ============

def add_alert(token_address: str, alert_type: str, message: str, 
              score: int = None, threshold_type: str = None):
    """Create an alert record"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO alerts (token_address, alert_type, message, score, threshold_type)
        VALUES (?, ?, ?, ?, ?)
    """, (token_address, alert_type, message, score, threshold_type))
    
    conn.commit()
    alert_id = cursor.lastrowid
    conn.close()
    
    return alert_id

def get_unacknowledged_alerts():
    """Get alerts that haven't been acknowledged"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alerts WHERE acknowledged = 0 ORDER BY created_at DESC")
    alerts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return alerts

def acknowledge_alert(alert_id: int):
    """Mark an alert as acknowledged"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE alerts SET acknowledged = 1 WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()

# ============ PIPELINE RUNS ============

def log_pipeline_run(tokens_fetched: int, opportunities_found: int, 
                     alerts_sent: int, status: str = "success",
                     error_message: str = None, duration_seconds: float = None):
    """Log a pipeline execution"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO pipeline_runs 
        (tokens_fetched, opportunities_found, alerts_sent, status, error_message, duration_seconds)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (tokens_fetched, opportunities_found, alerts_sent, status, error_message, duration_seconds))
    
    conn.commit()
    run_id = cursor.lastrowid
    conn.close()
    
    return run_id

def get_recent_runs(limit: int = 10):
    """Get recent pipeline runs"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pipeline_runs ORDER BY run_timestamp DESC LIMIT ?", (limit,))
    runs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return runs

# ============ ANALYTICS ============

def get_token_summary():
    """Get summary statistics"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT t.address) as total_tokens,
            COUNT(ps.id) as total_snapshots,
            AVG(ps.score) as avg_score,
            MAX(ps.captured_at) as last_update
        FROM tokens t
        LEFT JOIN price_snapshots ps ON t.address = ps.token_address
    """)
    
    summary = dict(cursor.fetchone())
    conn.close()
    return summary

def get_top_performers(hours: int = 24, limit: int = 10):
    """Get best performing tokens by score"""
    conn = get_connection()
    cursor = conn.cursor()
    cutoff = datetime.now() - timedelta(hours=hours)
    
    cursor.execute("""
        SELECT symbol, name, address, AVG(score) as avg_score, MAX(score) as max_score
        FROM price_snapshots
        WHERE captured_at > ?
        GROUP BY token_address
        ORDER BY avg_score DESC
        LIMIT ?
    """, (cutoff.isoformat(), limit))
    
    performers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return performers
