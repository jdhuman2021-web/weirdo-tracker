"""
Database CLI Tool
Query the SQLite database from command line

Usage:
    python db_cli.py tokens          - List all tokens
    python db_cli.py prices SYMBOL   - Get price history for token
    python db_cli.py summary         - Show database summary
    python db_cli.py top 10          - Top 10 performers
"""

import sys
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_queries import (
    get_all_tokens,
    get_price_history,
    get_latest_prices,
    get_token_summary,
    get_top_performers,
    add_token,
    get_connection
)

def cmd_tokens():
    """List all tokens"""
    tokens = get_all_tokens()
    print(f"Tokens ({len(tokens)} total):")
    print("-" * 80)
    for t in tokens:
        print(f"  {t['symbol']:15} {t['name'][:30]:30} {t['address'][:8]}...")

def cmd_prices(symbol: str):
    """Get price history for token"""
    tokens = get_all_tokens()
    token = next((t for t in tokens if t['symbol'].upper() == symbol.upper()), None)
    
    if not token:
        print(f"Token '{symbol}' not found")
        return
    
    history = get_price_history(token['address'], hours=24)
    print(f"Price history for {symbol} ({len(history)} snapshots):")
    print("-" * 80)
    for h in history[:10]:  # Show last 10
        print(f"  {h['captured_at'][:19]}  ${h['price_usd']:.6f}  MC:${h['market_cap']:,.0f}  Score:{h['score']}")

def cmd_summary():
    """Show database summary"""
    summary = get_token_summary()
    print("Database Summary:")
    print("-" * 80)
    print(f"  Total tokens:     {summary.get('total_tokens', 0)}")
    print(f"  Total snapshots:  {summary.get('total_snapshots', 0)}")
    print(f"  Average score:    {summary.get('avg_score', 0):.1f}")
    print(f"  Last update:      {summary.get('last_update', 'N/A')}")

def cmd_top(limit: int = 10):
    """Show top performers"""
    top = get_top_performers(hours=24, limit=limit)
    print(f"Top {limit} Performers (24h):")
    print("-" * 80)
    for i, t in enumerate(top, 1):
        print(f"  {i}. {t['symbol']:15} Avg Score: {t['avg_score']:.1f}  Max: {t['max_score']}")

def cmd_set_status(symbol: str, status: str):
    """Mark a token as dead or active"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Find token
    cursor.execute("SELECT id, symbol, address, status FROM tokens WHERE symbol = ?", (symbol.upper(),))
    token = cursor.fetchone()
    
    if not token:
        print(f"Token '{symbol}' not found")
        conn.close()
        return
    
    # Update status
    cursor.execute("UPDATE tokens SET status = ? WHERE id = ?", (status, token['id']))
    conn.commit()
    
    print(f"✅ {token['symbol']} marked as '{status}'")
    print(f"   Address: {token['address']}")
    print(f"   Previous status: {token['status']}")
    
    conn.close()

def cmd_list_dead():
    """List all dead tokens"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT symbol, name, address, status FROM tokens WHERE status = 'dead'")
    dead = cursor.fetchall()
    
    print(f"Dead Tokens ({len(dead)} total):")
    print("-" * 80)
    for t in dead:
        print(f"  {t[0]:15} {t[1][:30]:30} {t[2][:8]}...")
    
    conn.close()

def print_help():
    """Print usage help"""
    print("Database CLI Tool")
    print("-" * 80)
    print("Usage: python db_cli.py <command> [args]")
    print()
    print("Commands:")
    print("  tokens          - List all tokens")
    print("  prices SYMBOL   - Get price history for token")
    print("  summary         - Show database summary")
    print("  top [N]         - Top N performers (default: 10)")
    print("  dead            - List dead tokens")
    print("  set-status SYMBOL STATUS  - Mark token dead/active")
    print("  help            - Show this help")
    print()
    print("Examples:")
    print("  python db_cli.py set-status DRIVEI dead")
    print("  python db_cli.py set-status POUCH active")
    print("  python db_cli.py dead")

def main():
    if len(sys.argv) < 2:
        print_help()
        return
    
    cmd = sys.argv[1].lower()
    
    if cmd == 'tokens':
        cmd_tokens()
    elif cmd == 'prices' and len(sys.argv) >= 3:
        cmd_prices(sys.argv[2])
    elif cmd == 'summary':
        cmd_summary()
    elif cmd == 'top':
        limit = int(sys.argv[2]) if len(sys.argv) >= 3 else 10
        cmd_top(limit)
    elif cmd == 'dead':
        cmd_list_dead()
    elif cmd == 'set-status' and len(sys.argv) >= 4:
        cmd_set_status(sys.argv[2], sys.argv[3])
    elif cmd == 'help':
        print_help()
    else:
        print(f"Unknown command: {cmd}")
        print_help()

if __name__ == "__main__":
    main()
