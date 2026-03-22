"""
SolanaTracker Agent v1.0
Fetches token data from SolanaTracker API

API Docs: https://docs.solanatracker.io
Free tier: Available (rate limits apply)
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value.strip()

API_KEY = os.environ.get('SOLANATRACKER_API_KEY', '')
BASE_URL = 'https://data.solanatracker.io'


def fetch_token_data(token_address):
    """Fetch token data from SolanaTracker"""
    if not API_KEY:
        print("ERROR: SOLANATRACKER_API_KEY not found")
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
            print(f"  Rate limited for {token_address[:8]}...")
            return None
        else:
            print(f"  Error {response.status_code} for {token_address[:8]}...")
            return None
    except Exception as e:
        print(f"  Exception: {e}")
        return None


def load_config():
    """Load token configuration"""
    config_path = Path(__file__).parent.parent / "config" / "tokens.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        tokens = [t for t in config.get("tokens", []) if t.get("status", "active") != "dead"]
        return tokens
    except FileNotFoundError:
        print("ERROR: config/tokens.json not found")
        return []


def main():
    """Main execution"""
    print("SolanaTracker Agent v1.0")
    print("=" * 60)
    
    if not API_KEY:
        print("ERROR: SOLANATRACKER_API_KEY not set")
        print("Add it to your .env file: SOLANATRACKER_API_KEY=your_key")
        return False
    
    print(f"API Key: {API_KEY[:8]}...{API_KEY[-4:]}")
    print()
    
    # Load tokens
    tokens = load_config()
    print(f"Processing {len(tokens)} tokens...")
    print()
    
    # Fetch data for each token
    results = []
    success = 0
    failed = 0
    
    for i, token in enumerate(tokens, 1):
        symbol = token.get('symbol', 'UNKNOWN')
        address = token['address']
        
        print(f"[{i}/{len(tokens)}] {symbol}...", end=' ')
        
        data = fetch_token_data(address)
        if data:
            results.append({
                'symbol': symbol,
                'address': address,
                'data': data
            })
            success += 1
            
            # Extract key metrics from pools
            pools = data.get('pools', [])
            if pools:
                pool = pools[0]  # Get first pool
                price = pool.get('price', {}).get('usd', 0)
                market_cap = pool.get('marketCap', {}).get('usd', 0)
                volume = pool.get('txns', {}).get('volume24h', 0)
                liquidity = pool.get('liquidity', {}).get('usd', 0)
                print(f"OK ${price:.6f} | MC: ${market_cap:,.0f} | Vol: ${volume:,.0f} | Liq: ${liquidity:,.0f}")
            else:
                print(f"OK (no pools)")
        else:
            failed += 1
            print("FAILED")
        
        # Rate limiting - be gentle with free tier
        if i < len(tokens):
            time.sleep(2)  # Increased from 0.5 to 2 seconds
    
    # Save results
    output = {
        'timestamp': datetime.utcnow().isoformat(),
        'tokens_processed': len(tokens),
        'successful': success,
        'failed': failed,
        'results': results
    }
    
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    with open(data_dir / "solanatracker_data.json", 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("=" * 60)
    print(f"Processed: {len(tokens)} tokens")
    print(f"Successful: {success}")
    print(f"Failed: {failed}")
    print(f"Saved to: data/solanatracker_data.json")
    
    return success > 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
