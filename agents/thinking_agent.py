# Thinking agent.py

"""
Thinking Agent v2.0 - Advanced Opportunity Scoring
Focuses on whale accumulation signals and entry timing
"""

import json
from datetime import datetime
from pathlib import Path

def calculate_score(token):
    """
    Calculate opportunity score 0-100
    
    Scoring Philosophy:
    - We want tokens where WHALES are accumulating at LOWS
    - We want ORGANIC GROWTH (holders increasing)
    - We want SAFE EXITS (healthy liquidity)
    - We want EARLY ENTRY (fresh but not too fresh)
    - We want MOMENTUM SHIFT (price stabilizing after drop)
    """
    score = 0
    reasons = []
    risk_factors = []
    
    # ============================================
    # 1. PRICE POSITION (35 points max)
    # ============================================
    # We want to buy AFTER a drop, when price is stabilizing
    price_24h = token.get('price_change_24h', 0)
    price_1h = token.get('price_change_1h', 0)
    
    # Sweet spot: down 20-40% but stabilizing (1h better than 24h)
    if price_24h < -30 and price_1h > -5:
        score += 35  # Perfect: crashed but stabilizing
        reasons.append("Price crashed -30%+ but stabilizing - whale accumulation zone")
    elif price_24h < -25 and price_1h > 0:
        score += 32  # Very good: down big, now green 1h
        reasons.append("Price down -25%+ with 1h reversal")
    elif price_24h < -20 and price_1h > -3:
        score += 28  # Good: significant drop, stabilizing
        reasons.append("Price down -20%+ entering accumulation zone")
    elif price_24h < -15:
        score += 20  # Moderate: decent drop
        reasons.append("Price down -15% - potential entry")
    elif price_24h > 50:
        score -= 15  # Penalize: already pumped, missed boat
        risk_factors.append("Already pumped +50% - late entry risk")
    
    # ============================================
    # 2. VOLUME/LIQUIDITY RATIO (35 points max)
    # ============================================
    # EXTREME VOLUME = BULLISH! Whale accumulation signal
    volume = token.get('volume_24h', 0)
    liquidity = token.get('liquidity_usd', 1)
    vol_ratio = volume / liquidity if liquidity > 0 else 0
    
    # EXTREME VOLUME IS GOOD - whales are accumulating!
    if vol_ratio > 10:
        score += 35  # Maximum! Extreme whale activity
        reasons.append(f"Volume {vol_ratio:.1f}x - EXTREME whale accumulation!")
    elif vol_ratio > 5.0:
        score += 32  # Very high - strong interest
        reasons.append(f"Volume {vol_ratio:.1f}x - viral momentum")
    elif 2.0 <= vol_ratio <= 5.0:
        score += 28  # Healthy accumulation
        reasons.append(f"Volume {vol_ratio:.1f}x liquidity - healthy accumulation")
    elif vol_ratio > 1.5:
        score += 20  # Good: above average
        reasons.append(f"Volume {vol_ratio:.1f}x - rising interest")
    elif vol_ratio > 1.0:
        score += 12  # Moderate: slightly above average
        reasons.append("Volume above liquidity - mild interest")
    else:
        score -= 10  # Penalize: dead token
        risk_factors.append("Volume below liquidity - dead/abandoned")
    
    # ============================================
    # 3. HOLDER DYNAMICS (25 points max)
    # ============================================
    # Growing holders = organic interest, not just whale manipulation
    holder_count = token.get('holder_count', 0)
    holder_growth = token.get('holder_growth_24h', 0)
    
    # Skip holder penalties if data is missing (API limitation)
    if holder_count == 0:
        score += 5  # Neutral - data unavailable, not penalized
        reasons.append("Holder data unavailable - using on-chain estimate")
    else:
        # Absolute holder count matters
        if holder_count > 500:
            score += 8  # Strong community
            reasons.append(f"{holder_count} holders - established base")
        elif holder_count > 200:
            score += 5  # Decent
            reasons.append(f"{holder_count} holders - growing")
        elif holder_count < 50:
            score -= 3  # Too early (only if we have real data)
            reasons.append(f"{holder_count} holders - very early")
        
        # Growth rate matters more
        if holder_growth > 20:
            score += 17  # Viral growth
            reasons.append(f"Holders +{holder_growth:.1f}% - viral adoption")
        elif holder_growth > 12:
            score += 14  # Strong growth
            reasons.append(f"Holders +{holder_growth:.1f}% - strong interest")
        elif holder_growth > 5:
            score += 8  # Moderate growth
            reasons.append(f"Holders +{holder_growth:.1f}% - steady growth")
        elif holder_growth < -5:
            score -= 10  # Losing holders
            risk_factors.append(f"Holders -{abs(holder_growth):.1f}% - abandonment")
    
    # ============================================
    # 4. LIQUIDITY SAFETY (15 points max)
    # ============================================
    # Can you exit? Don't get trapped
    if liquidity > 100000:
        score += 15  # Very safe
        reasons.append("High liquidity - easy exit")
    elif liquidity > 50000:
        score += 12  # Safe
        reasons.append("Good liquidity - manageable exit")
    elif liquidity > 25000:
        score += 8  # Acceptable
        reasons.append("Acceptable liquidity - moderate slippage")
    elif liquidity > 10000:
        score += 4  # Risky
        reasons.append("Low liquidity - high slippage risk")
        risk_factors.append("Liquidity <10K - exit difficulty")
    else:
        score -= 10  # Very risky
        risk_factors.append("Liquidity <5K - trapped capital risk")
    
    # ============================================
    # 5. MARKET CAP OPPORTUNITY (10 points max)
    # ============================================
    # Micro-caps have most room to grow
    mcap = token.get('market_cap', 0)
    
    if 0 < mcap < 50000:
        score += 10  # Perfect: micro-cap gem
        reasons.append(f"${mcap:.0f} MC - micro-cap gem potential")
    elif mcap < 200000:
        score += 8  # Very good
        reasons.append(f"${mcap:.0f} MC - small-cap opportunity")
    elif mcap < 1000000:
        score += 5  # Good
        reasons.append(f"${mcap:.0f} MC - moderate growth room")
    elif mcap > 10000000:
        score -= 5  # Limited upside
        risk_factors.append(f"${mcap:.0f} MC - limited 100x potential")
    
    # ============================================
    # 6. AGE/TIMING (5 points bonus/penalty)
    # ============================================
    # Fresh but not too fresh
    age_hours = token.get('age_hours', 0)
    
    if 6 <= age_hours <= 48:
        score += 5  # Sweet spot: proven but still fresh
        reasons.append(f"{age_hours}h old - proven but fresh")
    elif age_hours < 6:
        score -= 3  # Too fresh - risky
        risk_factors.append(f"{age_hours}h old - very fresh, unproven")
    elif age_hours > 168:  # 7 days
        score -= 2  # Old - may have already pumped
    
    # ============================================
    # 7. RISK ADJUSTMENTS
    # ============================================
    # Holder concentration risk
    top_holder_pct = token.get('top_holder_pct', 0)
    if top_holder_pct > 50:
        score -= 20  # Dangerous
        risk_factors.append(f"Top holder {top_holder_pct:.1f}% - rug risk")
    elif top_holder_pct > 30:
        score -= 10  # Concerning
        risk_factors.append(f"Top holder {top_holder_pct:.1f}% - concentration risk")
    elif top_holder_pct < 10:
        score += 3  # Healthy distribution
        reasons.append("Holder distribution healthy")
    
    # ============================================
    # 8. WHALE ACTIVITY BONUS (15 points max)
    # ============================================
    # Check if tracked whale wallets are accumulating
    whale_activity = token.get('whale_activity', {})
    if whale_activity:
        active_whales = whale_activity.get('active_whales', [])
        total_buys = whale_activity.get('total_buys', 0)
        
        if len(active_whales) > 0:
            score += 15  # Max bonus for any whale activity
            reasons.append(f"🐋 {len(active_whales)} tracked whales buying in 24h")
        elif total_buys > 0:
            score += 10  # Some activity
            reasons.append(f"🐋 Whale accumulation detected ({total_buys} buys)")
    
    # Final score capped at 100
    final_score = min(max(score, 0), 100)
    
    return final_score, reasons, risk_factors

def get_signal(score):
    """Convert score to signal with nuanced thresholds"""
    if score >= 85:
        return "STRONG_BUY", "🔥 Strong Buy"
    elif score >= 70:
        return "BUY", "💚 Buy"
    elif score >= 55:
        return "SPECULATIVE", "⚠️ Speculative"
    elif score >= 40:
        return "WATCH", "❄️ Watch"
    else:
        return "AVOID", "🛑 Avoid"

def main():
    """Main execution"""
    print("🧠 Thinking Agent v2.1 - Advanced Scoring + Whale Intelligence")
    print("=" * 60)
    
    # Read latest research data
    try:
        with open('data/latest.json', 'r') as f:
            research = json.load(f)
    except FileNotFoundError:
        print("❌ No research data found. Run Research Agent first.")
        return
    
    # Load whale activity data
    try:
        with open('data/whale_activity.json', 'r') as f:
            whale_data = json.load(f)
        whale_activity = whale_data.get('whale_activity', {})
        print("🐋 Loaded whale activity data")
    except FileNotFoundError:
        print("⚠️ No whale activity data (run Whale Activity Agent first)")
        whale_activity = {}
    
    tokens = research.get('raw_data', [])
    
    # Analyze each token
    opportunities = []
    for token in tokens:
        # Attach whale activity data
        token['whale_activity'] = whale_activity.get(token['symbol'], {})
        
        score, reasons, risk_factors = calculate_score(token)
        signal, label = get_signal(score)
        
        opp = {
            **token,
            'score': score,
            'signal': signal,
            'label': label,
            'reasons': reasons,
            'risk_factors': risk_factors,
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
            'buys': len([o for o in opportunities if o['signal'] == 'BUY']),
            'speculative': len([o for o in opportunities if o['signal'] == 'SPECULATIVE']),
            'watch': len([o for o in opportunities if o['signal'] == 'WATCH']),
            'avoid': len([o for o in opportunities if o['signal'] == 'AVOID']),
            'agent': 'thinking_v2.0'
        },
        'opportunities': opportunities
    }
    
    with open('data/opportunities.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    # Summary
    print(f"\n📊 Analysis Complete:")
    print(f"  Total tokens: {len(opportunities)}")
    print(f"  🔥 Strong Buys: {len([o for o in opportunities if o['signal'] == 'STRONG_BUY'])}")
    print(f"  💚 Buys: {len([o for o in opportunities if o['signal'] == 'BUY'])}")
    print(f"  ⚠️ Speculative: {len([o for o in opportunities if o['signal'] == 'SPECULATIVE'])}")
    print(f"  ❄️ Watch: {len([o for o in opportunities if o['signal'] == 'WATCH'])}")
    print(f"  🛑 Avoid: {len([o for o in opportunities if o['signal'] == 'AVOID'])}")
    
    if opportunities:
        print(f"\n🏆 Top 3 Opportunities:")
        for i, opp in enumerate(opportunities[:3], 1):
            print(f"\n  {i}. {opp['symbol']} - Score: {opp['score']}")
            print(f"     Signal: {opp['label']}")
            print(f"     Reasons: {', '.join(opp['reasons'][:2])}")
            if opp.get('risk_factors'):
                print(f"     Risks: {', '.join(opp['risk_factors'][:2])}")

if __name__ == "__main__":
    main()
