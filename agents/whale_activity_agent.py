# Whale Activity Agent v1.0 - Track 87 Whale Wallets
# Checks if tracked wallets are accumulating tokens

import json
import requests
from datetime import datetime
from pathlib import Path

def load_whale_wallets():
    """Load tracked whale wallets from JSON file"""
    try:
        with open('whale_wallets.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ whale_wallets.json not found")
        return []

def check_wallet_activity(wallet_address, token_address):
    """
    Check if wallet has bought token in last 24h
    Uses Birdeye API (free, no key needed)
    """
    try:
        # Birdeye API - get wallet transactions for token
        url = f"https://public-api.birdeye.so/defi/txs?address={wallet_address}&token={token_address}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return {'bought': False, 'count': 0}
        
        data = response.json()
        
        # Count buy transactions in last 24h
        buys_24h = 0
        now = datetime.utcnow().timestamp()
        day_ago = now - 86400
        
        transactions = data.get('data', {}).get('txs', [])
        for tx in transactions:
            tx_time = tx.get('time', 0)
            tx_type = tx.get('type', '')
            
            if tx_time > day_ago and 'buy' in tx_type.lower():
                buys_24h += 1
        
        return {'bought': buys_24h > 0, 'count': buys_24h}
        
    except Exception as e:
        print(f"Error checking wallet {wallet_address}: {e}")
        return {'bought': False, 'count': 0}

def analyze_whale_activity(tokens, whale_wallets):
    """
    Analyze which tokens have whale accumulation
    Returns token -> whale activity data
    """
    whale_activity = {}
    
    print("🐋 Checking Whale Activity...")
    
    for token in tokens:
        token_address = token.get('address', '')
        symbol = token.get('symbol', 'UNKNOWN')
        
        # Check each tracked wallet
        active_whales = []
        total_buys = 0
        
        for wallet in whale_wallets[:20]:  # Check first 20 wallets (rate limit)
            result = check_wallet_activity(wallet['trackedWalletAddress'], token_address)
            
            if result['bought']:
                active_whales.append({
                    'name': wallet['name'],
                    'address': wallet['trackedWalletAddress'],
                    'buys': result['count']
                })
                total_buys += result['count']
        
        whale_activity[symbol] = {
            'active_whales': active_whales,
            'total_buys': total_buys,
            'whale_score': min(total_buys * 10, 30)  # Max 30 pts
        }
        
        if active_whales:
            print(f"  {symbol}: {len(active_whales)} whales active, {total_buys} buys")
        else:
            print(f"  {symbol}: No whale activity")
    
    return whale_activity

def main():
    """Main execution"""
    print("🐋 Whale Activity Agent v1.0")
    print("=" * 60)
    
    # Load data
    whale_wallets = load_whale_wallets()
    print(f"Loaded {len(whale_wallets)} tracked wallets")
    
    # Load latest token data
    try:
        with open('data/latest.json', 'r') as f:
            research = json.load(f)
        tokens = research.get('raw_data', [])
        print(f"Analyzing {len(tokens)} tokens")
    except FileNotFoundError:
        print("❌ No research data found")
        return
    
    # Analyze whale activity
    whale_activity = analyze_whale_activity(tokens, whale_wallets)
    
    # Save results
    Path('data').mkdir(exist_ok=True)
    
    output = {
        'metadata': {
            'timestamp': datetime.utcnow().isoformat(),
            'wallets_checked': len(whale_wallets),
            'tokens_analyzed': len(tokens),
            'agent': 'whale_activity_v1.0'
        },
        'whale_activity': whale_activity
    }
    
    with open('data/whale_activity.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Saved whale activity to data/whale_activity.json")
    
    # Summary
    active_tokens = [k for k, v in whale_activity.items() if v['active_whales']]
    print(f"\n📊 Summary:")
    print(f"  Tokens with whale activity: {len(active_tokens)}")
    if active_tokens:
        print(f"  Most active: {active_tokens[0]} ({whale_activity[active_tokens[0]]['total_buys']} buys)")

if __name__ == "__main__":
    main()
