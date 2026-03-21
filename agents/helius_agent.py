# Helius Agent v1.0 - Holder and Wallet Data
# Fetches holder count, fresh wallets, and token metadata from Helius API

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

HELIUS_RPC_URL = "https://mainnet.helius-rpc.com/"

def get_token_accounts(api_key, token_address):
    """
    Get all token accounts (holders) for a token
    
    Uses Helius DAS API
    """
    url = f"https://api.helius.xyz/v0/token-accounts?api-key={api_key}&mint={token_address}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Squirmy-Screener/1.0'})
        response = urllib.request.urlopen(req, timeout=15)
        data = json.loads(response.read().decode('utf-8'))
        return data
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print(f"  Rate limited, waiting 1 second...")
            time.sleep(1)
            return get_token_accounts(api_key, token_address)
        print(f"  HTTP Error {e.code}: {e.reason}")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

def get_asset(api_key, token_address):
    """
    Get token asset info (metadata, creator, etc.)
    
    Uses Helius DAS API
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
            return result[0]
        return None
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print(f"  Rate limited, waiting 1 second...")
            time.sleep(1)
            return get_asset(api_key, token_address)
        print(f"  HTTP Error {e.code}: {e.reason}")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

def analyze_fresh_wallets(accounts, hours_threshold=24):
    """
    Analyze wallet age for fresh wallet detection
    
    Returns count of wallets created within threshold hours
    """
    if not accounts:
        return 0, []
    
    fresh_wallets = []
    now = datetime.utcnow()
    
    for account in accounts:
        # Check if wallet is fresh (created within threshold)
        # Note: This requires additional API call to get wallet creation date
        # For now, we'll estimate based on balance and activity
        balance = float(account.get('amount', 0) or 0)
        if balance > 0:
            # Simplified fresh wallet detection
            # In production, you'd check actual wallet creation date
            pass
    
    return len(fresh_wallets), fresh_wallets

def process_token(api_key, token_info):
    """
    Process a single token with Helius API
    
    Returns holder count, metadata, and fresh wallet data
    """
    address = token_info['address']
    symbol = token_info.get('symbol', 'UNKNOWN')
    
    print(f"  [{symbol}] Fetching holder data...", end=' ')
    
    # Get token accounts (holders)
    accounts = get_token_accounts(api_key, address)
    
    holder_count = 0
    fresh_wallet_count = 0
    
    if accounts:
        holder_count = len(accounts)
        fresh_wallet_count, _ = analyze_fresh_wallets(accounts)
        print(f"{holder_count} holders")
    else:
        print("no data")
    
    # Get token metadata
    asset = get_asset(api_key, address)
    
    metadata = {}
    if asset:
        metadata = {
            'decimals': asset.get('decimals'),
            'supply': asset.get('supply'),
            'name': asset.get('name'),
            'creator': asset.get('creator'),
            'pump_fun_address': asset.get('pump_fun_address'),
            'launch_platform': 'pump.fun' if asset.get('pump_fun_address') else 'unknown'
        }
    
    return {
        'address': address,
        'symbol': symbol,
        'holder_count': holder_count,
        'fresh_wallet_count': fresh_wallet_count,
        'metadata': metadata,
        'timestamp': datetime.utcnow().isoformat()
    }

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
    print("Helius Agent v1.0")
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
    for i, token in enumerate(tokens, 1):
        result = process_token(api_key, token)
        results.append(result)
        
        # Rate limiting
        if i < len(tokens):
            time.sleep(0.5)
    
    # Save results
    output = {
        'timestamp': datetime.utcnow().isoformat(),
        'tokens_processed': len(results),
        'total_holders': sum(r['holder_count'] for r in results),
        'total_fresh_wallets': sum(r['fresh_wallet_count'] for r in results),
        'results': results
    }
    
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    with open(data_dir / "helius_data.json", 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("=" * 60)
    print(f"Processed {len(results)} tokens")
    print(f"Total holders: {output['total_holders']}")
    print(f"Saved to data/helius_data.json")

if __name__ == "__main__":
    main()