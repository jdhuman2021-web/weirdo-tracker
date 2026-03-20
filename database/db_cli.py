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
    get_top_performers
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
    print("  help            - Show this help")

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
    elif cmd == 'help':
        print_help()
    else:
        print(f"Unknown command: {cmd}")
        print_help()

if __name__ == "__main__":
    main()
