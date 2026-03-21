# Research Agent v1.5 - Supabase Cloud Database
# Fetches token data from DexScreener and writes to Supabase

import json
import requests
import time
from datetime import datetime
from pathlib import Path
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import Supabase client (optional)
try:
    from database.supabase_client import get_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Note: Supabase not available, using JSON only")

def load_config():
    """Load token configuration from JSON file"""
    try:
        with open('config/tokens.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("ERROR: config/tokens.json not found")
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
        pair = max(pairs, key=lambda x: float(x.get('liquidity', {}).get('usd', 0) or 0))
        
        # Calculate age
        pair_created = pair.get('pairCreatedAt')
        if pair_created:
            age_ms = datetime.now().timestamp() * 1000 - pair_created
            age_hours = int(age_ms / (1000 * 60 * 60))
        else:
            age_hours = 0
        
        # Get holder count from Birdeye (optional)
        holder_count = 0
        try:
            birdeye_url = f"https://public-api.birdeye.so/defi/token_overview?address={token['address']}"
            birdeye_response = requests.get(birdeye_url, timeout=10)
            if birdeye_response.status_code == 200:
                birdeye_data = birdeye_response.json()
                holder_count = birdeye_data.get('data', {}).get('holder', 0)
        except:
            pass
        
        return {
            'symbol': token['symbol'],
            'name': token.get('name', token['symbol']),
            'address': token['address'],
            'chain': token.get('chain', 'SOL'),
            'status': token.get('status', 'active'),
            'price_usd': float(pair.get('priceUsd', 0) or 0),
            'price_change_1h': float(pair.get('priceChange', {}).get('h1', 0) or 0),
            'price_change_24h': float(pair.get('priceChange', {}).get('h24', 0) or 0),
            'volume_24h': float(pair.get('volume', {}).get('h24', 0) or 0),
            'liquidity_usd': float(pair.get('liquidity', {}).get('usd', 0) or 0),
            'market_cap': float(pair.get('fdv', 0) or pair.get('marketCap', 0) or 0),
            'holder_count': holder_count,
            'pair_created_at': pair_created,
            'age_hours': age_hours,
            'age_days': round(age_hours / 24, 1) if age_hours else 0,
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'dexscreener'
        }
    except Exception as e:
        print(f"  ERROR fetching {token['symbol']}: {e}")
        return None

def main():
    """Main execution"""
    print("Research Agent v1.5 - Supabase Cloud Database")
    print("=" * 50)
    
    # Initialize Supabase client
    supabase = None
    if SUPABASE_AVAILABLE:
        try:
            supabase = get_client()
            if supabase and supabase.is_connected():
                print("Connected to Supabase")
            else:
                print("Supabase not connected (check credentials)")
        except Exception as e:
            print(f"Supabase init error: {e}")
    
    # Load configuration
    config = load_config()
    all_tokens = config.get('tokens', [])
    
    # Filter out dead/inactive tokens
    tokens = [t for t in all_tokens if t.get('status', 'active') != 'dead']
    dead_count = len(all_tokens) - len(tokens)
    
    if dead_count > 0:
        print(f"Skipped {dead_count} dead/inactive tokens")
    
    if not tokens:
        print("No active tokens configured")
        return
    
    # Deduplicate
    seen_addresses = set()
    unique_tokens = []
    for token in tokens:
        if token['address'] in seen_addresses:
            continue
        seen_addresses.add(token['address'])
        unique_tokens.append(token)
    
    print(f"Loaded {len(unique_tokens)} active tokens")
    print()
    
    # Fetch data for all tokens
    results = []
    for i, token in enumerate(unique_tokens, 1):
        print(f"[{i}/{len(unique_tokens)}] {token['symbol']}...", end=' ')
        data = fetch_token_data(token)
        if data:
            results.append(data)
            print(f"OK ${data['price_usd']:.6f} (Age: {data['age_hours']}h)")
        else:
            print("FAILED")
        
        if i < len(unique_tokens):
            time.sleep(6)  # Rate limiting
    
    # Save to JSON (backup)
    Path('data').mkdir(exist_ok=True)
    output = {
        'metadata': {
            'timestamp': datetime.utcnow().isoformat(),
            'tokens_fetched': len(results),
            'total_configured': len(tokens),
            'agent': 'research_v1.5',
            'supabase': SUPABASE_AVAILABLE and supabase is not None
        },
        'raw_data': results
    }
    
    with open('data/latest.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nSaved {len(results)} tokens to data/latest.json")
    
    # Write to Supabase
    if supabase and supabase.is_connected():
        print("\nWriting to Supabase...")
        db_writes = 0
        for token in results:
            try:
                # Upsert token
                supabase.upsert_token(
                    symbol=token['symbol'],
                    name=token.get('name', ''),
                    address=token['address'],
                    chain=token.get('chain', 'SOL'),
                    source=token.get('source', 'unknown'),
                    notes=token.get('notes', ''),
                    status=token.get('status', 'active')
                )
                
                # Insert snapshot
                supabase.insert_snapshot(
                    token_address=token['address'],
                    price_usd=token.get('price_usd', 0),
                    market_cap=token.get('market_cap', 0),
                    volume_24h=token.get('volume_24h', 0),
                    liquidity_usd=token.get('liquidity_usd', 0),
                    price_change_1h=token.get('price_change_1h', 0),
                    price_change_24h=token.get('price_change_24h', 0),
                    holder_count=token.get('holder_count', 0),
                    age_hours=token.get('age_hours', 0),
                    score=0,  # Scored by thinking agent
                    signal='UNKNOWN'
                )
                db_writes += 1
            except Exception as e:
                print(f"  Error writing {token['symbol']}: {e}")
        
        print(f"Wrote {db_writes} snapshots to Supabase")
        
        # Log pipeline run
        try:
            supabase.log_pipeline_run(
                tokens_fetched=len(results),
                opportunities_found=0,
                alerts_sent=0,
                status='success'
            )
        except:
            pass
    
    if results:
        sorted_by_age = sorted(results, key=lambda x: x['age_hours'])
        print(f"\nFreshest: {sorted_by_age[0]['symbol']} ({sorted_by_age[0]['age_hours']}h)")
        print(f"Oldest: {sorted_by_age[-1]['symbol']} ({sorted_by_age[-1]['age_hours']}h)")

if __name__ == "__main__":
    main()