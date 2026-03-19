#!/usr/bin/env python3
"""
Fetch latest token data from DexScreener API.
"""

import requests
import json
import sys
import time

def fetch_dexscreener_data(contract_address):
    """Fetch token data from DexScreener API."""
    
    url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("pairs"):
            return {"error": "No pairs found for contract"}
        
        # Get the pair with highest liquidity
        pairs = data["pairs"]
        pair = max(pairs, key=lambda x: float(x.get("liquidity", {}).get("usd", 0) or 0))
        
        return {
            "price_usd": float(pair.get("priceUsd", 0)),
            "market_cap": int(float(pair.get("marketCap", 0))),
            "liquidity": int(float(pair.get("liquidity", {}).get("usd", 0) or 0)),
            "volume_24h": int(float(pair.get("volume", {}).get("h24", 0) or 0)),
            "price_change_1h": float(pair.get("priceChange", {}).get("h1", 0) or 0),
            "price_change_24h": float(pair.get("priceChange", {}).get("h24", 0) or 0),
            "dex": pair.get("dexId", "unknown"),
            "pair": pair.get("pairAddress", "")
        }
        
    except requests.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

def main():
    if len(sys.argv) < 2:
        print("Usage: fetch_updates.py <contract_address>")
        sys.exit(1)
    
    contract = sys.argv[1]
    
    # Rate limiting - simple delay
    time.sleep(0.5)
    
    data = fetch_dexscreener_data(contract)
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    main()