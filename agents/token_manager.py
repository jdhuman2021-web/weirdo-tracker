"""
Token Manager - Add/Remove tokens from config
"""

import json
import sys
from datetime import datetime
from pathlib import Path

CONFIG_FILE = 'config/tokens.json'

def load_config():
    """Load token configuration"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        Path('config').mkdir(exist_ok=True)
        return {"tokens": [], "whales": []}

def save_config(config):
    """Save token configuration"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"💾 Saved to {CONFIG_FILE}")

def add_token():
    """Interactive token addition"""
    print("\n" + "=" * 50)
    print("➕ Add New Token")
    print("=" * 50)
    
    symbol = input("Symbol (e.g., PUNCH): ").strip().upper()
    if not symbol:
        print("❌ Symbol required")
        return
    
    config = load_config()
    
    # Check if already exists
    if any(t['symbol'] == symbol for t in config['tokens']):
        print(f"⚠️  {symbol} already exists")
        return
    
    name = input("Name (e.g., パンチ): ").strip() or symbol
    address = input("Contract Address: ").strip()
    if not address:
        print("❌ Address required")
        return
    
    chain = input("Chain (SOL/ETH/BASE) [SOL]: ").strip().upper() or "SOL"
    source = input("Source (e.g., Rick Telegram): ").strip() or "manual"
    notes = input("Notes (optional): ").strip()
    
    new_token = {
        "symbol": symbol,
        "name": name,
        "address": address,
        "chain": chain,
        "added_date": datetime.now().strftime("%Y-%m-%d"),
        "source": source,
        "notes": notes
    }
    
    config['tokens'].append(new_token)
    save_config(config)
    
    print(f"\n✅ Added {symbol} to watchlist!")
    print(f"   Address: {address[:20]}...")
    print(f"   Chain: {chain}")
    print(f"\n🔄 Run Research Agent to fetch data for this token")

def list_tokens():
    """List all configured tokens"""
    config = load_config()
    tokens = config.get('tokens', [])
    
    print("\n" + "=" * 50)
    print(f"📋 Configured Tokens ({len(tokens)})")
    print("=" * 50)
    
    for i, token in enumerate(tokens, 1):
        print(f"\n{i}. {token['symbol']} - {token['name']}")
        print(f"   Address: {token['address'][:30]}...")
        print(f"   Chain: {token['chain']} | Added: {token.get('added_date', 'N/A')}")
        if token.get('notes'):
            print(f"   Notes: {token['notes']}")

def remove_token():
    """Remove a token"""
    config = load_config()
    tokens = config.get('tokens', [])
    
    if not tokens:
        print("⚠️  No tokens to remove")
        return
    
    list_tokens()
    
    symbol = input("\nEnter symbol to remove: ").strip().upper()
    
    original_count = len(tokens)
    config['tokens'] = [t for t in tokens if t['symbol'] != symbol]
    
    if len(config['tokens']) < original_count:
        save_config(config)
        print(f"✅ Removed {symbol}")
    else:
        print(f"❌ {symbol} not found")

def main():
    """Main menu"""
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == 'add':
            add_token()
        elif cmd == 'list':
            list_tokens()
        elif cmd == 'remove':
            remove_token()
        else:
            print("Usage: python token_manager.py [add|list|remove]")
    else:
        # Interactive mode
        print("\n" + "=" * 50)
        print("🧠 Weirdo Tracker - Token Manager")
        print("=" * 50)
        print("\n1. Add new token")
        print("2. List all tokens")
        print("3. Remove token")
        print("4. Exit")
        
        choice = input("\nSelect: ").strip()
        
        if choice == '1':
            add_token()
        elif choice == '2':
            list_tokens()
        elif choice == '3':
            remove_token()
        else:
            print("Goodbye!")

if __name__ == "__main__":
    main()
