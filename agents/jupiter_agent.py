"""
Jupiter Price Agent v1.0
Fetches real-time prices from Jupiter API for Solana tokens

Jupiter Price API v3:
- Free tier available
- Up to 50 tokens per request
- Requires API key (x-api-key header)
- Returns USD price + 24h change

Usage:
    python agents/jupiter_agent.py
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.error

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

JUPITER_PRICE_API = "https://api.jup.ag/price/v3"

def get_prices_batch(addresses, api_key=None, batch_size=50):
    """
    Fetch prices for multiple tokens from Jupiter API v3
    
    Args:
        addresses: List of token addresses (max 50)
        api_key: Jupiter API key (required)
        batch_size: Number of tokens per request (max 50)
    
    Returns:
        Dict of {address: {price_usd, price_change_24h, source}}
    """
    if not api_key:
        api_key = os.environ.get("JUPITER_API_KEY")
    
    if not api_key:
        print("ERROR: JUPITER_API_KEY not found in environment")
        return {}
    
    all_prices = {}
    
    # Split into batches
    for i in range(0, len(addresses), batch_size):
        batch = addresses[i:i + batch_size]
        ids = ",".join(batch)
        
        url = f"{JUPITER_PRICE_API}?ids={ids}"
        
        try:
            req = urllib.request.Request(url)
            req.add_header('x-api-key', api_key)
            req.add_header('User-Agent', 'Squirmy-Screener/1.0')
            
            response = urllib.request.urlopen(req, timeout=10)
            data = json.loads(response.read().decode('utf-8'))
            
            # Parse response
            for address, price_data in data.items():
                if price_data and "usdPrice" in price_data:
                    all_prices[address] = {
                        "price_usd": float(price_data["usdPrice"]),
                        "price_change_24h": float(price_data.get("priceChange24h", 0)),
                        "block_id": price_data.get("blockId"),
                        "decimals": price_data.get("decimals"),
                        "source": "jupiter",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    all_prices[address] = None
                    
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"  Rate limited, waiting 1 second...")
                time.sleep(1)
                continue
            else:
                print(f"  HTTP Error {e.code}: {e.reason}")
        except Exception as e:
            print(f"  Error fetching prices: {e}")
        
        # Rate limit: be nice to the API
        if i + batch_size < len(addresses):
            time.sleep(0.1)
    
    return all_prices

def load_token_list():
    """Load active tokens from config"""
    config_path = Path(__file__).parent.parent / "config" / "tokens.json"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Filter active tokens (Solana only for Jupiter)
        tokens = [
            t for t in config.get("tokens", [])
            if t.get("status", "active") != "dead" 
            and t.get("chain", "SOL") == "SOL"
        ]
        return tokens
    except FileNotFoundError:
        print("ERROR: config/tokens.json not found")
        return []

def main():
    """Main execution"""
    print("Jupiter Price Agent v1.0")
    print("=" * 60)
    print(f"API: {JUPITER_PRICE_API}")
    print()
    
    # Check API key
    api_key = os.environ.get("JUPITER_API_KEY")
    if not api_key:
        print("ERROR: JUPITER_API_KEY not found")
        print("Set JUPITER_API_KEY in .env file")
        return
    
    print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
    print()
    
    # Load tokens
    tokens = load_token_list()
    
    if not tokens:
        print("No tokens to process")
        return
    
    print(f"Fetching prices for {len(tokens)} Solana tokens...")
    print()
    
    # Get all addresses
    addresses = [t["address"] for t in tokens]
    symbol_lookup = {t["address"]: t.get("symbol", "UNKNOWN") for t in tokens}
    
    # Fetch prices
    print("Fetching from Jupiter API...")
    prices = get_prices_batch(addresses, api_key=api_key, batch_size=50)
    
    # Print results
    print()
    print("=" * 60)
    print("PRICE RESULTS:")
    print("=" * 60)
    
    success_count = 0
    failed_count = 0
    
    for token in tokens:
        address = token["address"]
        symbol = token.get("symbol", "UNKNOWN")
        
        price_data = prices.get(address)
        
        if price_data:
            price = price_data["price_usd"]
            change = price_data.get("price_change_24h", 0)
            change_str = f"+{change:.2f}%" if change >= 0 else f"{change:.2f}%"
            print(f"  {symbol:<12} ${price:.8f} ({change_str})")
            success_count += 1
        else:
            print(f"  {symbol:<12} [NO PRICE]")
            failed_count += 1
    
    print()
    print(f"Summary: {success_count} successful, {failed_count} failed")
    
    # Save to file
    output = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": "jupiter",
        "api_version": "v3",
        "total_tokens": len(tokens),
        "successful": success_count,
        "failed": failed_count,
        "prices": prices
    }
    
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    with open(data_dir / "jupiter_prices.json", 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"Saved to data/jupiter_prices.json")
    
    return output

if __name__ == "__main__":
    main()