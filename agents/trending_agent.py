# Trending agent.py

"""
Trending Agent v1.0 - Fetch Trending Tokens from DexScreener
Gets the hottest tokens right now based on volume, price action, and social buzz
"""

import json
import requests
from datetime import datetime
from pathlib import Path

def fetch_trending_tokens(chain="solana", limit=15):
    """
    Fetch trending tokens from DexScreener
    
    DexScreener tracks:
    - Volume spikes
    - Price momentum
    - Social mentions
    - Trader activity
    """
    try:
        # DexScreener trending endpoint
        url = f"https://api.dexscreener.com/latest/dex/tokens/{chain}"
        
        # Alternative: Use screener for trending pairs
        screener_url = "https://api.dexscreener.com/latest/dex/screener"
        
        # Get top gainers (trending by price action)
        response = requests.get(screener_url, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            return []
        
        data = response.json()
        
        # Extract pairs and filter for trending signals
        pairs = data.get('pairs', [])
        
        trending = []
        for pair in pairs[:limit]:
            # Calculate trending score
            volume_24h = pair.get('volume', {}).get('h24', 0)
            price_change_24h = pair.get('priceChange', {}).get('h24', 0)
            liquidity = pair.get('liquidity', {}).get('usd', 0)
            
            # Trending criteria:
            # - High volume (>50K)
            # - Strong price action (>20% or <-30% for accumulation)
            # - Decent liquidity (>10K)
            
            trending_score = 0
            
            if volume_24h > 500000:
                trending_score += 30
            elif volume_24h > 200000:
                trending_score += 20
            elif volume_24h > 50000:
                trending_score += 10
            
            if abs(price_change_24h) > 50:
                trending_score += 25
            elif abs(price_change_24h) > 30:
                trending_score += 15
            elif abs(price_change_24h) > 10:
                trending_score += 8
            
            if liquidity > 100000:
                trending_score += 15
            elif liquidity > 50000:
                trending_score += 10
            elif liquidity > 10000:
                trending_score += 5
            
            # Only include if trending score is decent
            if trending_score >= 30:
                token = {
                    'symbol': pair.get('baseToken', {}).get('symbol', 'UNKNOWN'),
                    'name': pair.get('baseToken', {}).get('name', 'Unknown'),
                    'address': pair.get('baseToken', {}).get('address', ''),
                    'chain': pair.get('chainId', 'solana'),
                    'price_usd': pair.get('priceUsd', 0),
                    'price_change_24h': price_change_24h,
                    'volume_24h': volume_24h,
                    'liquidity_usd': liquidity,
                    'market_cap': 0,  # DexScreener doesn't provide MC directly
                    'trending_score': trending_score,
                    'pair_url': pair.get('url', ''),
                    'fdv': pair.get('fdv', 0),
                    'timestamp': datetime.utcnow().isoformat()
                }
                trending.append(token)
        
        # Sort by trending score
        trending.sort(key=lambda x: x['trending_score'], reverse=True)
        
        return trending[:limit]
        
    except Exception as e:
        print(f"❌ Error fetching trending: {e}")
        return []

def main():
    """Main execution"""
    print("🔥 Trending Agent v1.0 - DexScreener Trending Tokens")
    print("=" * 60)
    
    trending = fetch_trending_tokens(chain="solana", limit=15)
    
    if not trending:
        print("❌ No trending tokens found")
        return
    
    print(f"\n🔥 Top {len(trending)} Trending Tokens:\n")
    
    for i, token in enumerate(trending, 1):
        print(f"{i}. {token['symbol']}")
        print(f"   Price: ${token['price_usd']:.6f}")
        print(f"   24h Change: {token['price_change_24h']:+.1f}%")
        print(f"   Volume 24h: ${token['volume_24h']:,.0f}")
        print(f"   Liquidity: ${token['liquidity_usd']:,.0f}")
        print(f"   Trending Score: {token['trending_score']}")
        print(f"   URL: {token['pair_url']}")
        print()
    
    # Save to file
    Path('data').mkdir(exist_ok=True)
    
    output = {
        'metadata': {
            'timestamp': datetime.utcnow().isoformat(),
            'chain': 'solana',
            'limit': 15,
            'agent': 'trending_v1.0'
        },
        'trending': trending
    }
    
    with open('data/trending.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"💾 Saved {len(trending)} trending tokens to data/trending.json")

if __name__ == "__main__":
    main()
