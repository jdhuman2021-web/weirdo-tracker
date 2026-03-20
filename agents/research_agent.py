# Research agent.py

"""
Research Agent v1.2 - Real Token Age Support
Fetches pairCreatedAt from DexScreener and calculates token age
"""

import json
import requests
import time
from datetime import datetime
from pathlib import Path

def load_config():
    """Load token configuration from JSON file"""
    try:
        with open('config/tokens.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ config/tokens.json not found. Creating default...")
        Path('config').mkdir(exist_ok=True)
        default = {"tokens": [], "whales": []}
        with open('config/tokens.json', 'w') as f:
            json.dump(default, f, indent=2)
        return default

def fetch_token_data(token):
    """Fetch data for single token from DexScreener"""
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{token['address']}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        pairs = data.get('pairs', [])
        if not pairs:
            return None
        
        # Get pair with highest liquidity
        pair = max(pairs, key=lambda x: x.get('liquidity', {}).get('usd', 0) or 0)
        
        # Calculate token age from pairCreatedAt
        pair_created_at = pair.get('pairCreatedAt', 0)
        age_hours = 0
        if pair_created_at > 0:
            created_dt = datetime.fromtimestamp(pair_created_at / 1000)
            age_delta = datetime.utcnow() - created_dt
            age_hours = int(age_delta.total_seconds() / 3600)
        
        return {
            'symbol': token['symbol'],
            'name': token['name'],
            'address': token['address'],
            'chain': token['chain'],
            'price_usd': float(pair.get('priceUsd', 0)),
            'price_change_1h': float(pair.get('priceChange', {}).get('h1', 0) or 0),
            'price_change_24h': float(pair.get('priceChange', {}).get('h24', 0) or 0),
            'volume_24h': float(pair.get('volume', {}).get('h24', 0) or 0),
            'liquidity_usd': float(pair.get('liquidity', {}).get('usd', 0) or 0),
            'market_cap': float(pair.get('fdv', 0) or pair.get('marketCap', 0) or 0),
            'pair_created_at': pair_created_at,
            'age_hours': age_hours,
            'age_days': round(age_hours / 24, 1),
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'dexscreener',
            'added_date': token.get('added_date'),
            'notes': token.get('notes', '')
        }
    except Exception as e:
        print(f"Error fetching {token['symbol']}: {e}")
        return None

def main():
    """Main execution"""
    print("🔍 Research Agent v1.2 - Real Token Age Support")
    print("=" * 50)
    
    # Load configuration
    config = load_config()
    tokens = config.get('tokens', [])
    
    if not tokens:
        print("⚠️ No tokens configured. Add tokens to config/tokens.json")
        return
    
    print(f"📋 Loaded {len(tokens)} tokens from config")
    print()
    
    # Fetch data for all tokens
    results = []
    for i, token in enumerate(tokens, 1):
        print(f"[{i}/{len(tokens)}] {token['symbol']}...", end=' ')
        data = fetch_token_data(token)
        if data:
            results.append(data)
            print(f"✓ ${data['price_usd']:.6f} (Age: {data['age_hours']}h)")
        else:
            print("✗ Failed")
        
        if i < len(tokens):
            time.sleep(6)  # Rate limiting
    
    # Save results
    Path('data').mkdir(exist_ok=True)
    
    output = {
        'metadata': {
            'timestamp': datetime.utcnow().isoformat(),
            'tokens_fetched': len(results),
            'total_configured': len(tokens),
            'agent': 'research_v1.2'
        },
        'raw_data': results
    }
    
    with open('data/latest.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Saved {len(results)} tokens to data/latest.json")
    
    if results:
        sorted_by_age = sorted(results, key=lambda x: x['age_hours'])
        print(f"\n👶 Freshest: {sorted_by_age[0]['symbol']} ({sorted_by_age[0]['age_hours']}h old)")
        print(f"🧠 Oldest: {sorted_by_age[-1]['symbol']} ({sorted_by_age[-1]['age_hours']}h old)")

if __name__ == "__main__":
    main()
