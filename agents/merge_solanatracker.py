"""
SolanaTracker Data Merger v1.0
Merges SolanaTracker data (holders, security, socials) into pipeline

This enhances the scoring with:
- Security metrics (LP burn, freeze/mint authority)
- Holder counts
- Social links (Twitter, Telegram, Website)
- Transaction pressure (buy/sell ratio)
- Token age
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_solanatracker_data():
    """Load cached SolanaTracker data"""
    data_path = Path(__file__).parent.parent / "data" / "solanatracker_data.json"
    if not data_path.exists():
        print("Warning: solanatracker_data.json not found")
        return {}
    
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create lookup by address
        lookup = {}
        for result in data.get('results', []):
            address = result.get('address', '').lower()
            if address:
                lookup[address] = result.get('data', {})
        
        return lookup
    except Exception as e:
        print(f"Error loading SolanaTracker data: {e}")
        return {}

def extract_security_score(token_data):
    """Calculate security score from 0-100"""
    score = 0
    risks = []
    
    pools = token_data.get('pools', [])
    if not pools:
        return 50, ["No pool data"]
    
    pool = pools[0]
    security = pool.get('security', {})
    
    # LP Burn (max 40 points)
    lp_burn = pool.get('lpBurn', 0)
    if lp_burn >= 100:
        score += 40
    elif lp_burn >= 95:
        score += 35
    elif lp_burn >= 90:
        score += 30
    elif lp_burn >= 80:
        score += 20
    elif lp_burn >= 50:
        score += 10
    else:
        score += 0
        risks.append(f"Low LP burn: {lp_burn}%")
    
    # Freeze Authority (30 points)
    if security.get('freezeAuthority') is None:
        score += 30
    else:
        risks.append("Freeze authority present")
    
    # Mint Authority (30 points)
    if security.get('mintAuthority') is None:
        score += 30
    else:
        risks.append("Mint authority present")
    
    return score, risks

def extract_holder_data(token_data):
    """Extract holder metrics"""
    holders = token_data.get('holders', 0)
    
    # Get token supply for concentration calculation
    pools = token_data.get('pools', [])
    if pools:
        supply = pools[0].get('tokenSupply', 0)
    else:
        supply = 0
    
    return {
        'holder_count': holders,
        'token_supply': supply
    }

def extract_social_links(token_data):
    """Extract social links from token metadata"""
    token = token_data.get('token', {})
    
    return {
        'twitter': token.get('twitter'),
        'telegram': token.get('telegram'),
        'website': token.get('website'),
        'image': token.get('image')
    }

def extract_transaction_metrics(token_data):
    """Extract buy/sell pressure"""
    pools = token_data.get('pools', [])
    if not pools:
        return {
            'buys': 0,
            'sells': 0,
            'total': 0,
            'volume_24h': 0,
            'buy_sell_ratio': 1.0
        }
    
    pool = pools[0]
    txns = pool.get('txns', {})
    
    buys = txns.get('buys', 0)
    sells = txns.get('sells', 0)
    
    ratio = buys / sells if sells > 0 else 1.0
    
    return {
        'buys': buys,
        'sells': sells,
        'total': txns.get('total', 0),
        'volume_24h': txns.get('volume24h', 0),
        'buy_sell_ratio': ratio
    }

def extract_token_age(token_data):
    """Calculate token age in days"""
    token = token_data.get('token', {})
    creation = token.get('creation', {})
    created_time = creation.get('created_time')
    
    if created_time:
        # Unix timestamp to days
        now = datetime.utcnow().timestamp()
        age_days = (now - created_time) / (60 * 60 * 24)
        return round(age_days, 1)
    
    return 0

def merge_solanatracker_data(opportunities):
    """Merge SolanaTracker data into opportunities"""
    st_data = load_solanatracker_data()
    
    if not st_data:
        print("No SolanaTracker data available for merging")
        return opportunities
    
    enhanced = []
    merged_count = 0
    
    for opp in opportunities:
        address = opp.get('address', '').lower()
        
        if address in st_data:
            token_data = st_data[address]
            
            # Security
            security_score, risks = extract_security_score(token_data)
            opp['security_score'] = security_score
            opp['security_risks'] = risks
            
            # Holders
            holder_data = extract_holder_data(token_data)
            opp['holder_count'] = holder_data['holder_count']
            opp['token_supply'] = holder_data['token_supply']
            
            # Social links
            socials = extract_social_links(token_data)
            opp['socials'] = socials
            
            # Transaction metrics
            txns = extract_transaction_metrics(token_data)
            opp['txns_buys'] = txns['buys']
            opp['txns_sells'] = txns['sells']
            opp['txns_total'] = txns['total']
            opp['buy_sell_ratio'] = txns['buy_sell_ratio']
            
            # Token age
            opp['age_days'] = extract_token_age(token_data)
            
            # LP burn
            pools = token_data.get('pools', [])
            if pools:
                opp['lp_burn'] = pools[0].get('lpBurn', 0)
            
            merged_count += 1
        else:
            # No SolanaTracker data
            opp['security_score'] = 50
            opp['security_risks'] = ["No data"]
            opp['holder_count'] = 0
            opp['buy_sell_ratio'] = 1.0
            opp['age_days'] = opp.get('age_hours', 0) / 24 if opp.get('age_hours') else 0
            opp['lp_burn'] = 0
        
        enhanced.append(opp)
    
    print(f"Merged SolanaTracker data for {merged_count}/{len(opportunities)} tokens")
    return enhanced

if __name__ == "__main__":
    # Test with current opportunities
    opps_path = Path(__file__).parent.parent / "data" / "opportunities.json"
    
    if opps_path.exists():
        with open(opps_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        opportunities = data.get('opportunities', [])
        enhanced = merge_solanatracker_data(opportunities)
        
        # Save back
        data['opportunities'] = enhanced
        data['metadata']['solanatracker_merged'] = True
        data['metadata']['solanatracker_timestamp'] = datetime.utcnow().isoformat()
        
        with open(opps_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print("\n✓ SolanaTracker data merged successfully")
        
        # Show sample
        if enhanced:
            sample = enhanced[0]
            print(f"\nSample: {sample['symbol']}")
            print(f"  Security Score: {sample.get('security_score')}")
            print(f"  Holders: {sample.get('holder_count')}")
            print(f"  LP Burn: {sample.get('lp_burn')}%")
            print(f"  Buy/Sell Ratio: {sample.get('buy_sell_ratio'):.2f}")
            print(f"  Age: {sample.get('age_days')} days")
    else:
        print("No opportunities.json found")