"""
SolanaTracker Optimized Agent v2.0

Strategy:
- STATIC data (security, socials, creation date): Fetch once, cache forever
- DYNAMIC data (holders, transactions): Fetch every 2-3 days

This reduces credit usage by ~55% while keeping critical metrics fresh.
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Set UTF-8 encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

API_KEY = os.environ.get('SOLANATRACKER_API_KEY', '')
BASE_URL = 'https://data.solanatracker.io'
CACHE_FILE = Path(__file__).parent.parent / "data" / "solanatracker_cache.json"


def load_cache():
    """Load cached static data"""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {'tokens': {}, 'last_updated': {}}


def save_cache(cache):
    """Save cache to disk"""
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2)


def fetch_token_data(token_address):
    """Fetch token data from SolanaTracker"""
    if not API_KEY:
        return None
    
    url = f"{BASE_URL}/tokens/{token_address}"
    headers = {
        'x-api-key': API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            print(f"  Rate limited")
            return None
        else:
            return None
    except Exception as e:
        print(f"  Error: {e}")
        return None


def extract_static_data(token_data):
    """Extract static data (security, socials, creation)"""
    if not token_data:
        return {}
    
    token = token_data.get('token', {})
    pools = token_data.get('pools', [])
    
    if not pools:
        return {}
    
    pool = pools[0]
    security = pool.get('security', {})
    creation = token.get('creation', {})
    
    # Calculate security score
    lp_burn = pool.get('lpBurn', 0)
    score = 0
    if lp_burn >= 100: score = 40
    elif lp_burn >= 95: score = 35
    elif lp_burn >= 90: score = 30
    elif lp_burn >= 80: score = 20
    elif lp_burn >= 50: score = 10
    
    if security.get('freezeAuthority') is None: score += 30
    if security.get('mintAuthority') is None: score += 30
    
    return {
        'security_score': score,
        'lp_burn': lp_burn,
        'freeze_authority': security.get('freezeAuthority'),
        'mint_authority': security.get('mintAuthority'),
        'twitter': token.get('twitter'),
        'telegram': token.get('telegram'),
        'website': token.get('website'),
        'image': token.get('image'),
        'creation_time': creation.get('created_time'),
        'deployer': pool.get('deployer'),
        'static_fetched': datetime.utcnow().isoformat()
    }


def extract_dynamic_data(token_data):
    """Extract dynamic data (holders, transactions)"""
    if not token_data:
        return {}
    
    pools = token_data.get('pools', [])
    if not pools:
        return {}
    
    pool = pools[0]
    txns = pool.get('txns', {})
    
    buys = txns.get('buys', 0)
    sells = txns.get('sells', 0)
    ratio = buys / sells if sells > 0 else 1.0
    
    return {
        'holders': token_data.get('holders', 0),
        'token_supply': pool.get('tokenSupply', 0),
        'buys': buys,
        'sells': sells,
        'total_txns': txns.get('total', 0),
        'volume_24h': txns.get('volume24h', 0),
        'buy_sell_ratio': ratio,
        'dynamic_fetched': datetime.utcnow().isoformat()
    }


def should_refresh_dynamic(cache, token_address):
    """Check if dynamic data needs refresh (every 2-3 days)"""
    if token_address not in cache['tokens']:
        return True
    
    token_cache = cache['tokens'][token_address]
    last_dynamic = token_cache.get('dynamic_fetched')
    
    if not last_dynamic:
        return True
    
    last_time = datetime.fromisoformat(last_dynamic)
    days_since = (datetime.utcnow() - last_time).days
    
    # Refresh every 2 days
    return days_since >= 2


def main():
    """Main execution with optimized fetching"""
    print("SolanaTracker Optimized Agent v2.0")
    print("=" * 60)
    print("Strategy: Static data (once) + Dynamic data (every 2 days)")
    print("=" * 60)
    
    if not API_KEY:
        print("ERROR: SOLANATRACKER_API_KEY not set")
        return False
    
    # Load config
    config_path = Path(__file__).parent.parent / "config" / "tokens.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    tokens = [t for t in config['tokens'] if t.get('status') != 'dead']
    print(f"\nProcessing {len(tokens)} tokens...")
    
    # Load cache
    cache = load_cache()
    
    results = []
    static_fetched = 0
    dynamic_fetched = 0
    skipped = 0
    
    for i, token in enumerate(tokens, 1):
        symbol = token['symbol']
        address = token['address']
        
        print(f"[{i}/{len(tokens)}] {symbol}...", end=' ')
        
        # Check if we have this token in cache
        if address in cache['tokens']:
            cached = cache['tokens'][address]
            
            # Check if we need dynamic refresh
            if should_refresh_dynamic(cache, address):
                print("refreshing dynamic", end=' ')
                data = fetch_token_data(address)
                if data:
                    dynamic = extract_dynamic_data(data)
                    cached.update(dynamic)
                    dynamic_fetched += 1
                else:
                    print("(failed)", end=' ')
            else:
                print("using cache", end=' ')
                skipped += 1
            
            results.append({
                'symbol': symbol,
                'address': address,
                'data': cached
            })
            print("OK")
            
        else:
            # New token - fetch everything
            print("NEW TOKEN - fetching all", end=' ')
            data = fetch_token_data(address)
            
            if data:
                static = extract_static_data(data)
                dynamic = extract_dynamic_data(data)
                static.update(dynamic)
                
                cache['tokens'][address] = static
                results.append({
                    'symbol': symbol,
                    'address': address,
                    'data': static
                })
                static_fetched += 1
                dynamic_fetched += 1
                print("OK")
            else:
                print("FAILED")
        
        # Rate limiting
        if i < len(tokens):
            time.sleep(2)
    
    # Save cache
    save_cache(cache)
    
    # Save results
    output = {
        'timestamp': datetime.utcnow().isoformat(),
        'tokens_processed': len(tokens),
        'static_fetched': static_fetched,
        'dynamic_fetched': dynamic_fetched,
        'skipped': skipped,
        'results': results
    }
    
    data_dir = Path(__file__).parent.parent / "data"
    with open(data_dir / "solanatracker_data.json", 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("=" * 60)
    print(f"Processed: {len(tokens)} tokens")
    print(f"Static data (new): {static_fetched}")
    print(f"Dynamic refresh: {dynamic_fetched}")
    print(f"Skipped (cached): {skipped}")
    print(f"Est. credits used: {static_fetched + dynamic_fetched}")
    print(f"Saved to: data/solanatracker_cache.json")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
