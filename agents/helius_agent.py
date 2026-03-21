"""
Helius Agent v1.1 - Fixed API Endpoints
Fetches holder data, wallet info, and transaction history from Helius API

Helius provides:
- Holder count (via DAS API)
- Token metadata
- Transaction history
- Fresh wallet detection

Free tier: 100K credits/month

Usage:
    python agents/helius_agent.py
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import urllib.request
import urllib.error

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

def get_token_accounts(api_key, token_address):
    """
    Get holder count using Helius DAS API
    
    Endpoint: https://api.helius.xyz/v0/token-accounts
    """
    url = f"https://api.helius.xyz/v0/token-accounts?api-key={api_key}&mint={token_address}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Squirmy-Screener/1.0'})
        response = urllib.request.urlopen(req, timeout=15)
        data = json.loads(response.read().decode('utf-8'))
        
        # Count unique holders
        holders = data.get('result', {}).get('token_accounts', [])
        holder_count = len(holders) if holders else 0
        
        return {
            'holder_count': holder_count,
            'accounts': holders[:10]  # First 10 for analysis
        }
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {e.reason}")
        if e.code == 404:
            print(f"  Token {token_address[:8]}... not found")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

def get_asset_metadata(api_key, token_address):
    """
    Get token metadata using Helius DAS API
    
    Endpoint: https://api.helius.xyz/v0/token-metadata
    """
    url = f"https://api.helius.xyz/v0/token-metadata?api-key={api_key}"
    
    payload = {
        "mintAccounts": [token_address],
        "includeOffChain": True,
        "disableCache": False
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={
            'Content-Type': 'application/json',
            'User-Agent': 'Squirmy-Screener/1.0'
        })
        response = urllib.request.urlopen(req, timeout=15)
        result = json.loads(response.read().decode('utf-8'))
        
        if result and len(result) > 0:
            token_data = result[0]
            return {
                'decimals': token_data.get('decimals'),
                'supply': token_data.get('supply'),
                'name': token_data.get('name'),
                'symbol': token_data.get('symbol'),
                'creator': token_data.get('creator'),
                'pump_fun_address': token_data.get('pump_fun_address'),
                'launch_platform': 'pump.fun' if token_data.get('pump_fun_address') else 'unknown'
            }
        return None
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {e.reason}")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

def process_token(api_key, token_info):
    """
    Process a single token with Helius API
    """
    address = token_info['address']
    symbol = token_info.get('symbol', 'UNKNOWN')
    
    print(f"  [{symbol}] Fetching...", end=' ')
    
    # Get holder count
    holder_data = get_token_accounts(api_key, address)
    
    holder_count = 0
    if holder_data:
        holder_count = holder_data.get('holder_count', 0)
        print(f"{holder_count} holders", end=' ')
    else:
        print("no holder data", end=' ')
    
    # Get metadata
    metadata = get_asset_metadata(api_key, address)
    
    result = {
        'address': address,
        'symbol': symbol,
        'holder_count': holder_count,
        'fresh_wallet_count': 0,  # Requires additional API calls
        'metadata': metadata or {},
        'timestamp': datetime.utcnow().isoformat()
    }
    
    print()
    return result

def load_config():
    """Load token configuration"""
    config_path = Path(__file__).parent.parent / "config" / "tokens.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("ERROR: config/tokens.json not found")
        return {"tokens": []}

def main():
    """Main execution"""
    print("Helius Agent v1.1")
    print("=" * 60)
    print()
    
    # Check API key
    api_key = os.environ.get("HELIUS_API_KEY")
    if not api_key:
        print("ERROR: HELIUS_API_KEY not found in .env")
        return
    
    print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
    print()
    
    # Load config
    config = load_config()
    tokens = [t for t in config.get("tokens", []) if t.get("status", "active") != "dead"]
    
    print(f"Processing {len(tokens)} tokens...")
    print()
    
    # Process each token
    results = []
    success = 0
    failed = 0
    
    for i, token in enumerate(tokens, 1):
        result = process_token(api_key, token)
        results.append(result)
        
        if result.get('holder_count', 0) > 0:
            success += 1
        else:
            failed += 1
        
        # Rate limiting
        if i < len(tokens):
            time.sleep(0.5)
    
    # Save results
    output = {
        'timestamp': datetime.utcnow().isoformat(),
        'tokens_processed': len(results),
        'successful': success,
        'failed': failed,
        'total_holders': sum(r.get('holder_count', 0) for r in results),
        'results': results
    }
    
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    with open(data_dir / "helius_data.json", 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("=" * 60)
    print(f"Processed: {len(results)} tokens")
    print(f"Successful: {success}")
    print(f"Failed: {failed}")
    print(f"Total holders: {output['total_holders']}")
    print(f"Saved to: data/helius_data.json")

if __name__ == "__main__":
    main()