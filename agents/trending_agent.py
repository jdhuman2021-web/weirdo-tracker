# Trending agent.py

"""
Trending Agent v1.0 - Fetch Trending Tokens from DexScreener
Gets the hottest tokens right now based on volume, price action, and social buzz
"""

import json
import requests
from datetime import datetime
from pathlib import Path

def fetch_trending_tokens(chain="solana", limit=20):
    """
    Fetch trending tokens from DexScreener
    
    Uses multiple signals:
    - Top gainers (24h price action)
    - Volume leaders
    - Fresh tokens (< 7 days)
    """
    try:
        # DexScreener screener endpoint with Solana filter
        screener_url = "https://api.dexscreener.com/latest/dex/screener"
        
        response = requests.get(screener_url, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            return []
        
        data = response.json()
        pairs = data.get('pairs', [])
        
        # Filter for Solana only
        solana_pairs = [p for p in pairs if p.get('chainId') == 'solana']
        
        trending = []
        for pair in solana_pairs[:50]:  # Check more pairs
            # Extract data
            volume_24h = pair.get('volume', {}).get('h24', 0)
            price_change_24h = pair.get('priceChange', {}).get('h24', 0)
            liquidity = pair.get('liquidity', {}).get('usd', 0)
            fdv = pair.get('fdv', 0)
            
            # Calculate trending score
            trending_score = 0
            
            # Volume scoring (whale activity)
            if volume_24h > 1000000:
                trending_score += 35  # Extreme volume
            elif volume_24h > 500000:
                trending_score += 30
            elif volume_24h > 200000:
                trending_score += 20
            elif volume_24h > 50000:
                trending_score += 10
            
            # Price momentum (strong moves)
            if abs(price_change_24h) > 100:
                trending_score += 30  # Extreme mover
            elif abs(price_change_24h) > 50:
                trending_score += 25
            elif abs(price_change_24h) > 30:
                trending_score += 15
            elif abs(price_change_24h) > 10:
                trending_score += 8
            
            # Liquidity (safety)
            if liquidity > 100000:
                trending_score += 15
            elif liquidity > 50000:
                trending_score += 10
            elif liquidity > 10000:
                trending_score += 5
            
            # Market cap opportunity (micro-caps preferred)
            if 0 < fdv < 100000:
                trending_score += 10  # Micro-cap gem
            elif fdv < 500000:
                trending_score += 8
            
            # Only include if trending score is decent (minimum 35)
            if trending_score >= 35:
                token = {
                    'symbol': pair.get('baseToken', {}).get('symbol', 'UNKNOWN'),
                    'name': pair.get('baseToken', {}).get('name', 'Unknown'),
                    'address': pair.get('baseToken', {}).get('address', ''),
                    'chain': pair.get('chainId', 'solana'),
                    'price_usd': float(pair.get('priceUsd', 0) or 0),
                    'price_change_24h': price_change_24h,
                    'volume_24h': volume_24h,
                    'liquidity_usd': liquidity,
                    'market_cap': fdv,  # Use FDV as market cap estimate
                    'trending_score': trending_score,
                    'pair_url': pair.get('url', ''),
                    'fdv': fdv,
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
            'limit': 20,
            'agent': 'trending_v1.1'
        },
        'trending': trending
    }
    
    with open('data/trending.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"💾 Saved {len(trending)} trending tokens to data/trending.json")
    
    # Save to history (persist trending history)
    history_file = Path('data/trending_history.json')
    history = []
    
    if history_file.exists():
        with open(history_file, 'r') as f:
            history = json.load(f)
    
    # Add this run to history
    history_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'count': len(trending),
        'top_token': trending[0]['symbol'] if trending else None,
        'tokens': trending
    }
    
    history.append(history_entry)
    
    # Keep last 100 entries (about 2 days of history at 30-min intervals)
    history = history[-100:]
    
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)
    
    print(f"📜 Saved trending history ({len(history)} entries)")

if __name__ == "__main__":
    main()
