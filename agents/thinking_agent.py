# Thinking Agent v2.4 - Fixed Volume Scoring + Whale Priority
# Uses Supabase price history for trend analysis + whale intelligence

import json
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def calculate_score(token, price_history=None, whale_data=None):
    """
    Calculate opportunity score 0-100
    
    Scoring Philosophy:
    - We want tokens where WHALES are accumulating at LOWS
    - We want ORGANIC GROWTH (holders increasing)
    - We want SAFE EXITS (healthy liquidity)
    - We want EARLY ENTRY (fresh but not too fresh)
    - We want MOMENTUM SHIFT (price stabilizing after drop)
    
    FIXED: Volume ratio now considers whale activity BEFORE penalizing
    
    Args:
        token: Token data dict
        price_history: List of historical price snapshots
        whale_data: Whale activity data dict
    """
    score = 0
    reasons = []
    risk_factors = []
    
    # ============================================
    # Pre-check: Whale activity (for volume scoring)
    # ============================================
    has_whale_activity = False
    if whale_data:
        vol_1h_ratio = whale_data.get('vol_1h_ratio', 0)
        vol_5m_ratio = whale_data.get('vol_5m_ratio', 0)
        has_whale_activity = whale_data.get('whale_activity_detected', False) or vol_1h_ratio > 1.5 or vol_5m_ratio > 2.0
    
    # ============================================
    # 1. PRICE POSITION (35 points max)
    # ============================================
    price_24h = token.get('price_change_24h', 0)
    price_1h = token.get('price_change_1h', 0)
    
    # MASSIVE CRASH = AVOID (rug pull or dead)
    if price_24h < -50:
        score -= 20
        risk_factors.append(f"Crashed {abs(price_24h):.0f}% in 24h - likely rug pull or dead")
    # Controlled dip with recovery = BUY
    elif price_24h < -30 and price_1h > 0:
        score += 25
        reasons.append("Price down -30%+ with 1h reversal - potential bounce")
    elif price_24h < -25 and price_1h > -3:
        score += 20
        reasons.append("Price down -25%+ stabilizing - accumulation zone")
    elif price_24h < -20 and price_1h > -5:
        score += 18
        reasons.append("Price down -20% entering dip zone")
    elif price_24h < -15:
        score += 12
        reasons.append("Price down -15% - minor correction")
    elif price_24h < -10:
        score += 5
        reasons.append("Price down -10% - small dip")
    elif 0 <= price_24h <= 30:
        score += 5
        reasons.append("Price stable or trending up")
    elif price_24h > 30 and price_24h <= 100:
        score -= 5
        risk_factors.append(f"Already pumped +{price_24h:.0f}% - higher risk")
    elif price_24h > 100:
        score -= 15
        risk_factors.append(f"Extreme pump +{price_24h:.0f}% - very late entry risk")
    
    # ============================================
    # 2. VOLUME/LIQUIDITY RATIO (35 points max)
    # FIXED: Check whale activity before penalizing low volume
    # ============================================
    volume = token.get('volume_24h', 0)
    liquidity = token.get('liquidity_usd', 1)
    vol_ratio = volume / liquidity if liquidity > 0 else 0
    
    # EXTREME VOLUME IS GOOD - whales are accumulating!
    if vol_ratio > 10:
        score += 35
        reasons.append(f"Volume {vol_ratio:.1f}x - EXTREME whale accumulation!")
    elif vol_ratio > 5.0:
        score += 32
        reasons.append(f"Volume {vol_ratio:.1f}x - viral momentum")
    elif 2.0 <= vol_ratio <= 5.0:
        score += 28
        reasons.append(f"Volume {vol_ratio:.1f}x liquidity - healthy accumulation")
    elif vol_ratio > 1.5:
        score += 20
        reasons.append(f"Volume {vol_ratio:.1f}x - rising interest")
    elif vol_ratio > 1.0:
        score += 12
        reasons.append("Volume above liquidity - mild interest")
    elif vol_ratio > 0.5:
        score += 5
        reasons.append("Moderate trading activity")
    elif has_whale_activity:
        # Whale activity detected - don't penalize low volume!
        # Whales are buying despite low overall volume
        score += 10
        reasons.append("🐋 Whale activity detected - smart money accumulating")
    else:
        # No whale activity + low volume = check market cap
        mcap = token.get('market_cap', 0)
        if mcap > 1000000:
            # Established token with $1M+ MC - stable, not dead
            score -= 3
            reasons.append("Lower volume - established token")
        elif mcap > 100000:
            # Mid-cap $100K-$1M - might be dormant
            score -= 5
            risk_factors.append("Low volume relative to liquidity")
        else:
            # Small MC + low volume = likely dead/abandoned
            score -= 10
            risk_factors.append("Volume below liquidity - dead/abandoned")
    
    # ============================================
    # 3. HOLDER DYNAMICS (25 points max)
    # ============================================
    holder_count = token.get('holder_count', 0)
    holder_growth = token.get('holder_growth_24h', 0)
    
    if holder_count == 0:
        score += 5
        reasons.append("Holder data unavailable - using on-chain estimate")
    else:
        if holder_count > 500:
            score += 8
            reasons.append(f"{holder_count} holders - established base")
        elif holder_count > 200:
            score += 5
            reasons.append(f"{holder_count} holders - growing")
        elif holder_count < 50:
            score -= 3
            reasons.append(f"{holder_count} holders - very early")
        
        if holder_growth > 20:
            score += 17
            reasons.append(f"Holders +{holder_growth:.1f}% - viral adoption")
        elif holder_growth > 12:
            score += 14
            reasons.append(f"Holders +{holder_growth:.1f}% - strong interest")
        elif holder_growth > 5:
            score += 8
            reasons.append(f"Holders +{holder_growth:.1f}% - steady growth")
        elif holder_growth < -5:
            score -= 10
            risk_factors.append(f"Holders -{abs(holder_growth):.1f}% - abandonment")
    
    # ============================================
    # 4. LIQUIDITY SAFETY (15 points max)
    # ============================================
    if liquidity > 100000:
        score += 15
        reasons.append("High liquidity - easy exit")
    elif liquidity > 50000:
        score += 12
        reasons.append("Good liquidity - manageable exit")
    elif liquidity > 25000:
        score += 8
        reasons.append("Acceptable liquidity - moderate slippage")
    elif liquidity > 10000:
        score += 4
        reasons.append("Low liquidity - high slippage risk")
        risk_factors.append("Liquidity <10K - exit difficulty")
    else:
        score -= 10
        risk_factors.append("Liquidity <5K - trapped capital risk")
    
    # ============================================
    # 5. MARKET CAP OPPORTUNITY (10 points max)
    # ============================================
    mcap = token.get('market_cap', 0)
    
    if 0 < mcap < 50000:
        score += 10
        reasons.append(f"${mcap:.0f} MC - micro-cap gem potential")
    elif mcap < 200000:
        score += 8
        reasons.append(f"${mcap:.0f} MC - small-cap opportunity")
    elif mcap < 1000000:
        score += 5
        reasons.append(f"${mcap:.0f} MC - moderate growth room")
    elif mcap > 10000000:
        score -= 5
        risk_factors.append(f"${mcap:.0f} MC - limited 100x potential")
    
    # ============================================
    # 6. AGE/TIMING (5 points bonus/penalty)
    # ============================================
    age_hours = token.get('age_hours', 0)
    
    if 6 <= age_hours <= 48:
        score += 5
        reasons.append(f"{age_hours}h old - proven but fresh")
    elif age_hours < 6:
        score -= 3
        risk_factors.append(f"{age_hours}h old - very fresh, unproven")
    elif age_hours > 168:
        score -= 2
    
    # ============================================
    # 7. HISTORICAL TREND (15 points max)
    # ============================================
    if price_history and len(price_history) >= 3:
        try:
            prices = [p.get('price_usd', 0) for p in price_history if p.get('price_usd', 0) > 0]
            
            if len(prices) >= 3:
                recent_avg = sum(prices[:3]) / len(prices[:3])
                older_avg = sum(prices[3:min(6, len(prices))]) / len(prices[3:min(6, len(prices))]) if len(prices) > 3 else recent_avg
                
                if recent_avg > older_avg * 1.15:
                    score += 15
                    reasons.append("📈 Strong uptrend from historical lows")
                elif recent_avg > older_avg * 1.05:
                    score += 10
                    reasons.append("📈 Price trending up from recent lows")
                elif recent_avg < older_avg * 0.85:
                    score -= 10
                    risk_factors.append("📉 Price trending down - momentum weak")
                elif recent_avg < older_avg * 0.95:
                    score -= 5
                    risk_factors.append("📉 Price declining from historical average")
                
                if len(prices) >= 5:
                    avg_price = sum(prices) / len(prices)
                    variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
                    volatility = (variance ** 0.5) / avg_price if avg_price > 0 else 0
                    
                    if volatility > 0.5:
                        score -= 5
                        risk_factors.append(f"High volatility ({volatility*100:.0f}%) - unstable")
        except Exception as e:
            print(f"  Error calculating historical trend: {e}")
    
    # ============================================
    # 8. WHALE ACTIVITY BONUS (20 points max)
    # ============================================
    if whale_data:
        vol_1h_ratio = whale_data.get('vol_1h_ratio', 0)
        vol_5m_ratio = whale_data.get('vol_5m_ratio', 0)
        whale_detected = whale_data.get('whale_activity_detected', False)
        
        if whale_detected:
            if vol_1h_ratio > 3.0:
                score += 20
                reasons.append(f"🐋 EXTREME whale volume {vol_1h_ratio:.1f}x")
            elif vol_1h_ratio > 2.0:
                score += 15
                reasons.append(f"🐋 Whale accumulation detected {vol_1h_ratio:.1f}x")
            elif vol_5m_ratio > 5.0:
                score += 15
                reasons.append(f"🐋 Active whale buying NOW {vol_5m_ratio:.1f}x")
            elif vol_5m_ratio > 3.0:
                score += 10
                reasons.append(f"🐋 Recent whale activity {vol_5m_ratio:.1f}x")
            else:
                score += 5
                reasons.append("🐋 Whale activity detected")
            
            # Check for whale selling
            if vol_1h_ratio > 2.0 and price_1h < -10:
                score -= 15
                risk_factors.append(f"🐋 Whale selling (vol {vol_1h_ratio:.1f}x, price {price_1h:.0f}%)")
    
    # ============================================
    # Final Score Capping
    # ============================================
    final_score = max(0, min(100, score))
    
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
    print("Thinking Agent v2.4 - Fixed Volume Scoring + Whale Priority")
    print("=" * 60)
    
    # Import Supabase client
    supabase = None
    try:
        from database.supabase_client import get_client
        supabase = get_client()
        if supabase and supabase.is_connected():
            print("✅ Connected to Supabase")
        else:
            print("⚠️ Supabase not connected - using JSON only")
            supabase = None
    except Exception as e:
        print(f"⚠️ Supabase import error: {e}")
    
    # Read latest research data
    try:
        with open('data/latest.json', 'r', encoding='utf-8') as f:
            research = json.load(f)
    except FileNotFoundError:
        print("ERROR: No research data found. Run Research Agent first.")
        return
    
    # Load whale activity data
    whale_activity = {}
    try:
        with open('data/whale_activity.json', 'r', encoding='utf-8') as f:
            whale_data = json.load(f)
            whale_activity = whale_data.get('whale_activity', {})
        print(f"✅ Loaded whale activity for {len(whale_activity)} tokens")
    except FileNotFoundError:
        print("⚠️ No whale activity data (run Whale Agent first)")
    
    tokens = research.get('raw_data', [])
    tokens = [t for t in tokens if t.get('status', 'active') != 'dead']
    
    # Analyze each token
    opportunities = []
    
    for i, token in enumerate(tokens, 1):
        symbol = token['symbol']
        address = token['address']
        
        print(f"[{i}/{len(tokens)}] Scoring {symbol}...", end=' ')
        
        # Get price history from Supabase
        price_history = []
        if supabase:
            try:
                price_history = supabase.get_price_history(address, hours=24) or []
                if price_history:
                    print(f"({len(price_history)} snapshots)", end=' ')
            except Exception as e:
                print(f"(history error)", end=' ')
        
        # Get whale data
        whale_data = whale_activity.get(address, {})
        
        # Calculate score
        score, reasons, risk_factors = calculate_score(
            token, 
            price_history=price_history,
            whale_data=whale_data
        )
        
        signal, label = get_signal(score)
        
        opp = {
            **token,
            'score': score,
            'signal': signal,
            'label': label,
            'reasons': reasons,
            'risk_factors': risk_factors,
            'historical_snapshots': len(price_history),
            'analyzed_at': datetime.utcnow().isoformat()
        }
        opportunities.append(opp)
        
        print(f"→ {score} {signal}")
    
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
            'agent': 'thinking_v2.4',
            'supabase_connected': supabase is not None
        },
        'opportunities': opportunities
    }
    
    Path('data').mkdir(exist_ok=True)
    with open('data/opportunities.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    # Summary
    print(f"\n{'=' * 60}")
    print("Analysis Complete:")
    print(f"  Total tokens: {len(opportunities)}")
    print(f"  🔥 Strong Buys: {output['metadata']['strong_buys']}")
    print(f"  💚 Buys: {output['metadata']['buys']}")
    print(f"  ⚠️ Speculative: {output['metadata']['speculative']}")
    print(f"  ❄️ Watch: {output['metadata']['watch']}")
    print(f"  🛑 Avoid: {output['metadata']['avoid']}")
    
    if opportunities:
        print(f"\n🏆 Top 3 Opportunities:")
        for i, opp in enumerate(opportunities[:3], 1):
            print(f"\n  {i}. {opp['symbol']} - Score: {opp['score']}")
            print(f"     Signal: {opp['label']}")
            if opp.get('reasons'):
                print(f"     Reasons: {', '.join(opp['reasons'][:2])}")
            if opp.get('risk_factors'):
                print(f"     Risks: {', '.join(opp['risk_factors'][:2])}")
    
    # Write scores to Supabase
    if supabase and supabase.is_connected():
        print("\nWriting scores to Supabase...")
        for opp in opportunities[:10]:
            try:
                supabase.client.table('price_snapshots').update({
                    'score': opp['score'],
                    'signal': opp['signal']
                }).eq('token_address', opp['address']).order('captured_at', desc=True).limit(1).execute()
            except Exception as e:
                print(f"  Error updating {opp['symbol']}: {e}")
        
        print("✅ Scores written to Supabase")

if __name__ == "__main__":
    main()