#!/usr/bin/env python3
"""
Research Agent v1.0
Fetches market data from DexScreener API for Weirdo Tracker
"""

import json
import time
import os
from datetime import datetime
from typing import Dict, List, Optional
import requests
from config import TOKENS, WHALE_WALLETS, DEXSCREENER_API, DATA_DIR

class ResearchAgent:
    """Agent responsible for gathering raw market data"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WeirdoTracker/1.0 (Research Agent)'
        })
        self.data_dir = DATA_DIR
        os.makedirs(self.data_dir, exist_ok=True)
    
    def fetch_token_data(self, token: Dict) -> Optional[Dict]:
        """Fetch live data for a single token from DexScreener"""
        try:
            url = f"{DEXSCREENER_API}/tokens/{token['address']}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            pairs = data.get('pairs', [])
            
            if not pairs:
                print(f"⚠️  No pairs found for {token['symbol']}")
                return None
            
            # Get the most liquid pair
            pair = max(pairs, key=lambda x: x.get('liquidity', {}).get('usd', 0) or 0)
            
            return {
                'symbol': token['symbol'],
                'name': token['name'],
                'address': token['address'],
                'chain': token['chain'],
                'price_usd': float(pair.get('priceUsd', 0)),
                'price_change_1h': float(pair.get('priceChange', {}).get('h1', 0) or 0),
                'price_change_24h': float(pair.get('priceChange', {}).get('h24', 0) or 0),
                'volume_24h': float(pair.get('volume', {}).get('h24', 0) or 0),
                'liquidity_usd': float(pair.get('liquidity', {}).get('usd', 0) or 0),
                'market_cap': float(pair.get('fdv', 0) or pair.get('marketCap', 0) or 0),
                'txns_24h': {
                    'buys': int(pair.get('txns', {}).get('h24', {}).get('buys', 0) or 0),
                    'sells': int(pair.get('txns', {}).get('h24', {}).get('sells', 0) or 0)
                },
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'dexscreener'
            }
            
        except Exception as e:
            print(f"❌ Error fetching {token['symbol']}: {e}")
            return None
    
    def fetch_all_tokens(self) -> List[Dict]:
        """Fetch data for all tracked tokens"""
        print(f"🔍 Fetching data for {len(TOKENS)} tokens...")
        results = []
        
        for i, token in enumerate(TOKENS, 1):
            print(f"  [{i}/{len(TOKENS)}] {token['symbol']}...", end=' ')
            data = self.fetch_token_data(token)
            if data:
                results.append(data)
                print(f"✓ ${data['price_usd']:.6f}")
            else:
                print("✗ Failed")
            
            # Rate limiting - max 10 requests per minute
            if i < len(TOKENS):
                time.sleep(6)  # 6 seconds between requests
        
        return results
    
    def save_data(self, data: List[Dict], filename: str = None):
        """Save research data to JSON file"""
        if not filename:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"research_{timestamp}.json"
        
        filepath = os.path.join(self.data_dir, filename)
        
        output = {
            'metadata': {
                'timestamp': datetime.utcnow().isoformat(),
                'tokens_count': len(data),
                'source': 'research_agent_v1.0'
            },
            'data': data
        }
        
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n💾 Saved to {filepath}")
        return filepath
    
    def run(self):
        """Main execution loop"""
        print("=" * 50)
        print("🧠 Weirdo Tracker - Research Agent v1.0")
        print("=" * 50)
        print(f"⏰ Started at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print()
        
        # Fetch all token data
        results = self.fetch_all_tokens()
        
        if results:
            # Save to file
            filepath = self.save_data(results)
            
            # Print summary
            print("\n" + "=" * 50)
            print("📊 SUMMARY")
            print("=" * 50)
            print(f"Tokens fetched: {len(results)}/{len(TOKENS)}")
            
            # Top gainers/losers
            sorted_by_change = sorted(results, key=lambda x: x['price_change_24h'], reverse=True)
            
            print(f"\n🔥 Top Gainer: {sorted_by_change[0]['symbol']} (+{sorted_by_change[0]['price_change_24h']:.2f}%)")
            print(f"❄️ Top Loser: {sorted_by_change[-1]['symbol']} ({sorted_by_change[-1]['price_change_24h']:.2f}%)")
            
            # High volume tokens
            high_volume = [t for t in results if t['volume_24h'] > 100000]
            print(f"\n💧 High Volume (>$100K): {len(high_volume)} tokens")
            
            return filepath
        else:
            print("\n❌ No data fetched")
            return None


def main():
    """Entry point"""
    agent = ResearchAgent()
    agent.run()


if __name__ == "__main__":
    main()
