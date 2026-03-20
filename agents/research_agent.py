# Research agent.py

"""
Research Agent v1.3 - SQLite Database Support
Fetches pairCreatedAt from DexScreener, calculates token age, writes to DB
"""

import json
import requests
import time
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for db_queries import
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_config():
    """Load token configuration from JSON file"""
    try:
        with open('config/tokens.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("ERROR: config/tokens.json not found. Creating default...")
        Path('config').mkdir(exist_ok=True)
        default = {"tokens": [], "whales": []}
        with open('config/tokens.json', 'w', encoding='utf-8') as f:
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
        
        # Fetch holder count from Birdeye (free, no API key needed)
        holder_count = 0
        try:
            # Birdeye public API - no auth required
            birdeye_url = f"https://public-api.birdeye.so/defi/token_holder?address={token['address']}"
            holder_resp = requests.get(birdeye_url, timeout=5)
            if holder_resp.status_code == 200:
                holder_data = holder_resp.json()
                holder_count = holder_data.get('data', {}).get('totalHolders', 0)
                print(f"👥 {holder_count} holders")
        except Exception as e:
            # Fallback: estimate from transaction count
            txns_24h = pair.get('txns', {}).get('h24', {})
            if txns_24h:
                # Rough estimate: unique holders ≈ (buys + sells) / 3
                estimated = (txns_24h.get('buys', 0) + txns_24h.get('sells', 0)) // 3
                holder_count = max(estimated, 10)  # Minimum 10
            print(f"👥 ~{holder_count} holders (estimated)")
        
        return {
            'symbol': token['symbol'],
            'name': token['name'],
            'address': token['address'],
            'chain': token['chain'],
            'status': token.get('status', 'active'),
            'price_usd': float(pair.get('priceUsd', 0)),
            'price_change_1h': float(pair.get('priceChange', {}).get('h1', 0) or 0),
            'price_change_24h': float(pair.get('priceChange', {}).get('h24', 0) or 0),
            'volume_24h': float(pair.get('volume', {}).get('h24', 0) or 0),
            'liquidity_usd': float(pair.get('liquidity', {}).get('usd', 0) or 0),
            'market_cap': float(pair.get('fdv', 0) or pair.get('marketCap', 0) or 0),
            'holder_count': holder_count,
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
    print("Research Agent v1.3 - SQLite Database Support")
    print("=" * 50)
    
    # Import DB functions
    try:
        from database.db_queries import add_price_snapshot, get_all_tokens
        db_available = True
        print("Database module loaded OK")
    except Exception as e:
        print(f"Database module not available: {e}")
        db_available = False
    
    # Load configuration
    config = load_config()
    all_tokens = config.get('tokens', [])
    
    # Filter out dead/inactive tokens
    tokens = [t for t in all_tokens if t.get('status', 'active') != 'dead']
    dead_count = len(all_tokens) - len(tokens)
    
    if dead_count > 0:
        print(f"Skipped {dead_count} dead/inactive tokens")
    
    if not tokens:
        print("WARN: No active tokens configured. Add tokens to config/tokens.json")
        return
    
    # Deduplicate tokens by address (prevent duplicates from batch adds)
    seen_addresses = set()
    unique_tokens = []
    for token in tokens:
        if token['address'] in seen_addresses:
            print(f"Skipping duplicate: {token['symbol']} ({token['address'][:8]}...)")
            continue
        seen_addresses.add(token['address'])
        unique_tokens.append(token)
    
    print(f"Loaded {len(tokens)} tokens from config ({len(unique_tokens)} unique)")
    print()
    
    # Fetch data for all tokens
    results = []
    db_writes = 0
    for i, token in enumerate(unique_tokens, 1):
        print(f"[{i}/{len(unique_tokens)}] {token['symbol']}...", end=' ')
        data = fetch_token_data(token)
        if data:
            results.append(data)
            print(f"OK ${data['price_usd']:.6f} (Age: {data['age_hours']}h)")
            
            # Write to database if available
            if db_available:
                try:
                    add_price_snapshot(
                        token_address=data['address'],
                        price_usd=data['price_usd'],
                        market_cap=data['market_cap'],
                        volume_24h=data['volume_24h'],
                        liquidity_usd=data['liquidity_usd'],
                        price_change_1h=data['price_change_1h'],
                        price_change_24h=data['price_change_24h'],
                        holder_count=data.get('holder_count', 0),
                        age_hours=data.get('age_hours', 0),
                        score=0,  # Research agent doesn't score
                        signal='UNKNOWN'
                    )
                    db_writes += 1
                except Exception as e:
                    print(f"  DB write failed: {e}")
        else:
            print("FAILED")
        
        if i < len(unique_tokens):
            time.sleep(6)  # Rate limiting
    
    # Save results to JSON (for pipeline compatibility)
    Path('data').mkdir(exist_ok=True)
    
    output = {
        'metadata': {
            'timestamp': datetime.utcnow().isoformat(),
            'tokens_fetched': len(results),
            'total_configured': len(tokens),
            'agent': 'research_v1.3',
            'db_writes': db_writes
        },
        'raw_data': results
    }
    
    with open('data/latest.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nSaved {len(results)} tokens to data/latest.json")
    print(f"Database writes: {db_writes}")
    
    if results:
        sorted_by_age = sorted(results, key=lambda x: x['age_hours'])
        print(f"\nFreshest: {sorted_by_age[0]['symbol']} ({sorted_by_age[0]['age_hours']}h old)")
        print(f"Oldest: {sorted_by_age[-1]['symbol']} ({sorted_by_age[-1]['age_hours']}h old)")
        
        # Holder stats if available
        holders_data = [r for r in results if r.get('holder_count', 0) > 0]
        if holders_data:
            sorted_by_holders = sorted(holders_data, key=lambda x: x.get('holder_count', 0), reverse=True)
            print(f"\nMost Holders: {sorted_by_holders[0]['symbol']} ({sorted_by_holders[0]['holder_count']})")

if __name__ == "__main__":
    main()
