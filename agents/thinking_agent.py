# Thinking agent.py

"""
Thinking Agent v1.1 - Real Token Age Scoring
Uses actual token age from DexScreener
"""

import json
from datetime import datetime
from pathlib import Path

def calculate_score(token):
    """Calculate opportunity score 0-100"""
    score = 0
    reasons = []
    
    # Price drop from high (30 points max)
    if token.get('price_change_24h', 0) < -30:
        score += 30
        reasons.append("Price down >30% - potential reversal")
    elif token.get('price_change_24h', 0) < -20:
        score += 20
        reasons.append("Price down >20%")
    elif token.get('price_change_24h', 0) < -10:
        score += 10
        reasons.append("Price down >10%")
    
    # Volume spike (25 points max)
    volume = token.get('volume_24h', 0)
    liquidity = token.get('liquidity_usd', 1)
    vol_ratio = volume / liquidity if liquidity > 0 else 0
    
    if vol_ratio > 3:
        score += 25
        reasons.append(f"Volume {vol_ratio:.1f}x liquidity - accumulation")
    elif vol_ratio > 2:
        score += 15
        reasons.append(f"Volume {vol_ratio:.1f}x - rising interest")
    elif vol_ratio > 1:
        score += 5
        reasons.append("Volume above average")
    
    # Liquidity health (25 points max)
    if liquidity > 100000:
        score += 15
        reasons.append("High liquidity - easy exit")
    elif liquidity > 50000:
        score += 10
        reasons.append("Good liquidity")
    elif liquidity > 25000:
        score += 5
        reasons.append("Acceptable liquidity")
    
    # Market cap size (20 points max)
    mcap = token.get('market_cap', 0)
    if mcap < 1000000 and mcap > 0:
        score += 20
        reasons.append("Micro-cap - high growth potential")
    elif mcap < 5000000:
        score += 10
        reasons.append("Small-cap - growth opportunity")
    
    return min(score, 100), reasons

def get_signal(score):
    """Convert score to signal"""
    if score >= 80:
        return "STRONG_BUY", "🔥 Strong Buy"
    elif score >= 60:
        return "SPECULATIVE", "⚠️ Speculative"
    elif score >= 40:
        return "WATCH", "❄️ Watch"
    else:
        return "AVOID", "🛑 Avoid"

def main():
    """Main execution"""
    print("🧠 Thinking Agent v1.1 - Analyzing opportunities...")
    
    # Read latest research data
    try:
        with open('data/latest.json', 'r') as f:
            research = json.load(f)
    except FileNotFoundError:
        print("❌ No research data found. Run Research Agent first.")
        return
    
    tokens = research.get('raw_data', [])
    
    # Analyze each token
    opportunities = []
    for token in tokens:
        score, reasons = calculate_score(token)
        signal, label = get_signal(score)
        
        opp = {
            **token,
            'score': score,
            'signal': signal,
            'label': label,
            'reasons': reasons,
            'analyzed_at': datetime.utcnow().isoformat()
        }
        opportunities.append(opp)
    
    # Sort by score
    opportunities.sort(key=lambda x: x['score'], reverse=True)
    
    # Save scored data
    output = {
        'metadata': {
            'timestamp': datetime.utcnow().isoformat(),
            'total_opportunities': len(opportunities),
            'strong_buys': len([o for o in opportunities if o['signal'] == 'STRONG_BUY']),
            'agent': 'thinking_v1.1'
        },
        'opportunities': opportunities
    }
    
    with open('data/opportunities.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    # Summary
    print(f"\n📊 Analysis Complete:")
    print(f"  Total tokens: {len(opportunities)}")
    print(f"  🔥 Strong Buys: {len([o for o in opportunities if o['signal'] == 'STRONG_BUY'])}")
    print(f"  ⚠️ Speculative: {len([o for o in opportunities if o['signal'] == 'SPECULATIVE'])}")
    print(f"  ❄️ Watch: {len([o for o in opportunities if o['signal'] == 'WATCH'])}")
    print(f"  🛑 Avoid: {len([o for o in opportunities if o['signal'] == 'AVOID'])}")
    
    if opportunities:
        print(f"\n🏆 Top Opportunity:")
        top = opportunities[0]
        print(f"  {top['symbol']} - Score: {top['score']}")
        print(f"  {top['label']}")
        print(f"  Reasons: {', '.join(top['reasons'][:2])}")
        
        # Age stats
        if 'age_hours' in top:
            print(f"  Age: {top['age_hours']} hours ({top['age_days']} days)")

if __name__ == "__main__":
    main()
