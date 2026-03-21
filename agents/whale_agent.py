# Whale Tracking Agent v1.0
# Tracks whale activity using DexScreener transaction data

import json
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import Supabase client
try:
    from database.supabase_client import get_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("WARNING: Supabase client not available")

def load_config():
    """Load whale wallet configuration"""
    try:
        with open('config/tokens.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print("ERROR: config/tokens.json not found")
        return {"tokens": [], "whales": []}

def load_whale_wallets():
    """Load tracked whale wallets"""
    whale_file = Path('config/whale_wallets.json')
    if whale_file.exists():
        with open(whale_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Default whale wallets (you should add your own)
    return {
        "whales": [
            # These are example addresses - replace with real tracked wallets
            # {"address": "...", "name": "Whale1", "tags": ["whale", "early_investor"]},
        ]
    }

def get_token_transactions(address: str, limit: int = 50):
    """
    Fetch recent transactions for a token from DexScreener
    
    Note: DexScreener doesn't provide full transaction history,
    but we can infer whale activity from volume and price movements.
    For actual transaction tracking, consider:
    - Helius API (Solana)
    - Solscan API
    - Birdeye API (when working)
    """
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        pairs = data.get('pairs', [])
        if not pairs:
            return None
        
        # Get the main pair (highest liquidity)
        pair = max(pairs, key=lambda x: float(x.get('liquidity', {}).get('usd', 0) or 0))
        
        # Extract volume and price data
        volume_24h = float(pair.get('volume', {}).get('h24', 0) or 0)
        volume_1h = float(pair.get('volume', {}).get('h1', 0) or 0)
        volume_5m = float(pair.get('volume', {}).get('m5', 0) or 0)
        
        # Calculate volume ratios (whale indicators)
        vol_1h_vs_24h = (volume_1h * 24) / volume_24h if volume_24h > 0 else 0
        vol_5m_vs_1h = (volume_5m * 12) / volume_1h if volume_1h > 0 else 0
        
        # High volume in short period = potential whale activity
        is_whale_active = vol_1h_vs_24h > 2.0 or vol_5m_vs_1h > 3.0
        
        return {
            'address': address,
            'volume_24h': volume_24h,
            'volume_1h': volume_1h,
            'volume_5m': volume_5m,
            'vol_1h_ratio': round(vol_1h_vs_24h, 2),
            'vol_5m_ratio': round(vol_5m_vs_1h, 2),
            'whale_activity_detected': is_whale_active,
            'whale_confidence': 'high' if (vol_1h_vs_24h > 3.0 or vol_5m_vs_1h > 5.0) else 'medium' if is_whale_active else 'low'
        }
    except Exception as e:
        print(f"  ERROR fetching transactions for {address}: {e}")
        return None

def get_helius_transactions(address: str, helius_api_key: str = None):
    """
    Fetch transactions using Helius API (Solana-specific)
    
    Requires: Helius API key (free tier: 1M requests/month)
    Docs: https://docs.helius.dev/
    """
    api_key = helius_api_key or os.environ.get('HELIUS_API_KEY', '')
    
    if not api_key:
        return None
    
    try:
        url = f"https://api.helius.dev/v0/addresses/{address}/transactions"
        params = {'api-key': api_key}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        transactions = []
        
        for tx in data[:20]:  # Last 20 transactions
            # Parse transaction for large transfers
            if tx.get('type') == 'SWAP':
                native_transfers = tx.get('nativeTransfers', [])
                for transfer in native_transfers:
                    amount_usd = transfer.get('amount', 0) / 1e9  # Lamports to SOL
                    if amount_usd > 1000:  # > $1000
                        transactions.append({
                            'token_address': address,
                            'action': 'buy' if transfer.get('toUserAccount') else 'sell',
                            'amount_usd': amount_usd,
                            'timestamp': tx.get('timestamp'),
                            'signature': tx.get('signature'),
                            'whale_detected': True
                        })
        
        return transactions
    except Exception as e:
        print(f"  Helius API error: {e}")
        return None

def calculate_whale_signals(token_data: dict, whale_activity: dict):
    """
    Calculate whale activity signals from volume data
    
    Returns a score adjustment and reasons
    """
    score = 0
    reasons = []
    risk_factors = []
    
    vol_1h_ratio = whale_activity.get('vol_1h_ratio', 0)
    vol_5m_ratio = whale_activity.get('vol_5m_ratio', 0)
    confidence = whale_activity.get('whale_confidence', 'low')
    
    # High volume ratio in last hour
    if vol_1h_ratio > 3.0:
        score += 15
        reasons.append(f"🐋 EXTREME: Volume {vol_1h_ratio:.1f}x 24h avg - massive whale activity")
    elif vol_1h_ratio > 2.0:
        score += 10
        reasons.append(f"🐋 Volume {vol_1h_ratio:.1f}x 24h avg - whale accumulation")
    elif vol_1h_ratio > 1.5:
        score += 5
        reasons.append(f"🐋 Volume {vol_1h_ratio:.1f}x - increased interest")
    
    # High volume in last 5 minutes
    if vol_5m_ratio > 5.0:
        score += 10
        reasons.append(f"🐋 URGENT: Volume {vol_5m_ratio:.1f}x hourly avg - active buying NOW")
    elif vol_5m_ratio > 3.0:
        score += 5
        reasons.append(f"🐋 Volume spike {vol_5m_ratio:.1f}x - recent whale activity")
    
    # Adjust confidence
    if confidence == 'high':
        reasons.append("Whale confidence: HIGH")
    elif confidence == 'medium':
        reasons.append("Whale confidence: MEDIUM")
    
    # Check if whales are selling (price dropping with high volume)
    price_1h = token_data.get('price_change_1h', 0)
    price_24h = token_data.get('price_change_24h', 0)
    
    if vol_1h_ratio > 2.0 and price_1h < -10:
        # High volume + price drop = potential whale selling
        score -= 10
        risk_factors.append(f"🐋 Whale selling detected (vol {vol_1h_ratio:.1f}x, price {price_1h:.0f}%)")
    
    return score, reasons, risk_factors

def main():
    """Main execution"""
    print("Whale Tracking Agent v1.0")
    print("=" * 50)
    
    # Initialize Supabase
    supabase = None
    if SUPABASE_AVAILABLE:
        try:
            supabase = get_client()
            if supabase and supabase.is_connected():
                print("Connected to Supabase")
        except Exception as e:
            print(f"Supabase init error: {e}")
    
    # Load config
    config = load_config()
    tokens = [t for t in config.get('tokens', []) if t.get('status', 'active') != 'dead']
    
    # Load whale wallets
    whale_config = load_whale_wallets()
    tracked_whales = whale_config.get('whales', [])
    
    print(f"Loaded {len(tokens)} tokens")
    print(f"Tracking {len(tracked_whales)} whale wallets")
    print()
    
    # Analyze each token for whale activity
    whale_data = {}
    
    for i, token in enumerate(tokens, 1):
        symbol = token['symbol']
        address = token['address']
        
        print(f"[{i}/{len(tokens)}] {symbol}...", end=' ')
        
        # Get volume-based whale signals
        tx_data = get_token_transactions(address)
        
        if tx_data:
            whale_data[address] = tx_data
            status = "WHALE" if tx_data.get('whale_activity_detected') else "normal"
            print(f"{status} (vol ratio: {tx_data.get('vol_1h_ratio', 0):.1f}x)")
        else:
            print("FAILED")
        
        # Rate limiting
        if i < len(tokens):
            time.sleep(3)
    
    # Save whale activity data
    output = {
        'metadata': {
            'timestamp': datetime.utcnow().isoformat(),
            'tokens_analyzed': len(whale_data),
            'tokens_with_whale_activity': len([v for v in whale_data.values() if v.get('whale_activity_detected')]),
            'tracked_whales': len(tracked_whales),
            'agent': 'whale_tracker_v1.0'
        },
        'whale_activity': whale_data
    }
    
    Path('data').mkdir(exist_ok=True)
    with open('data/whale_activity.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Saved whale activity for {len(whale_data)} tokens")
    
    # Summary
    whale_tokens = [addr for addr, data in whale_data.items() if data.get('whale_activity_detected')]
    if whale_tokens:
        print(f"\n🐋 Tokens with Whale Activity:")
        for addr in whale_tokens[:5]:
            data = whale_data[addr]
            print(f"  {addr[:8]}... - Volume ratio: {data.get('vol_1h_ratio', 0):.1f}x")
    
    # Write to Supabase
    if supabase and supabase.is_connected():
        print("\nWriting whale activity to Supabase...")
        for addr, data in whale_data.items():
            if data.get('whale_activity_detected'):
                try:
                    supabase.insert_whale_activity(
                        token_address=addr,
                        whale_address='VOLUME_SPIKE',
                        whale_name='Volume Whale',
                        action='buy',  # Assumed buy on volume spike
                        amount_usd=data.get('volume_1h', 0)
                    )
                except Exception as e:
                    print(f"  Error writing whale data: {e}")
        
        print("✅ Whale activity saved to Supabase")
    
    return whale_data

if __name__ == "__main__":
    main()