# Alert agent.py

"""
Alert Agent v1.1 - Holder Spike Detection
Monitors holder growth and volume spikes
"""

import json
import os
from datetime import datetime
from pathlib import Path

def check_holder_spikes(opportunities, threshold=15):
    """Detect tokens with holder growth > threshold%"""
    alerts = []
    
    for token in opportunities:
        holder_growth = token.get('holder_growth_24h', 0)
        holder_count = token.get('holder_count', 0)
        
        if holder_growth > threshold and holder_count > 0:
            alerts.append({
                'type': 'HOLDER_SPIKE',
                'symbol': token['symbol'],
                'holder_count': holder_count,
                'holder_growth': holder_growth,
                'price_change_24h': token.get('price_change_24h', 0),
                'volume_24h': token.get('volume_24h', 0),
                'timestamp': datetime.utcnow().isoformat()
            })
    
    return alerts

def check_volume_spikes(opportunities, threshold=2.0):
    """Detect tokens with volume > threshold x liquidity"""
    alerts = []
    
    for token in opportunities:
        volume = token.get('volume_24h', 0)
        liquidity = token.get('liquidity_usd', 1)
        vol_ratio = volume / liquidity if liquidity > 0 else 0
        
        if vol_ratio > threshold:
            alerts.append({
                'type': 'VOLUME_SPIKE',
                'symbol': token['symbol'],
                'vol_ratio': vol_ratio,
                'volume_24h': volume,
                'liquidity_usd': liquidity,
                'timestamp': datetime.utcnow().isoformat()
            })
    
    return alerts

def check_holder_concentration(opportunities, top_holder_threshold=30):
    """Alert if top holder concentration is too high"""
    alerts = []
    
    for token in opportunities:
        top_holder_pct = token.get('top_holder_pct', 0)
        
        if top_holder_pct > top_holder_threshold:
            alerts.append({
                'type': 'HOLDER_CONCENTRATION',
                'symbol': token['symbol'],
                'top_holder_pct': top_holder_pct,
                'holder_count': token.get('holder_count', 0),
                'risk': 'HIGH' if top_holder_pct > 50 else 'MEDIUM',
                'timestamp': datetime.utcnow().isoformat()
            })
    
    return alerts

def send_telegram_alert(alert, bot_token, chat_id):
    """Send alert to Telegram"""
    if not bot_token or not chat_id:
        return False
    
    message = ""
    if alert['type'] == 'HOLDER_SPIKE':
        message = f"👥 HOLDER SPIKE ALERT\n\n"
        message += f"Token: {alert['symbol']}\n"
        message += f"Holders: {alert['holder_count']} (+{alert['holder_growth']:.1f}%)\n"
        message += f"24h: {alert['price_change_24h']:.1f}%\n"
        message += f"Vol: ${alert['volume_24h']:,.0f}"
    elif alert['type'] == 'VOLUME_SPIKE':
        message = f"📊 VOLUME SPIKE ALERT\n\n"
        message += f"Token: {alert['symbol']}\n"
        message += f"Vol Ratio: {alert['vol_ratio']:.1f}x liquidity\n"
        message += f"Volume: ${alert['volume_24h']:,.0f}"
    elif alert['type'] == 'HOLDER_CONCENTRATION':
        message = f"⚠️ HOLDER CONCENTRATION WARNING\n\n"
        message += f"Token: {alert['symbol']}\n"
        message += f"Top Holder: {alert['top_holder_pct']:.1f}%\n"
        message += f"Risk: {alert['risk']}\n"
        message += f"Holders: {alert['holder_count']}"
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        import requests
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
    except:
        return False

def main():
    """Main execution"""
    print("🚨 Alert Agent v1.1 - Holder Spike Detection")
    print("=" * 50)
    
    # Read opportunities data
    try:
        with open('data/opportunities.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ No opportunities data found. Run pipeline first.")
        return
    
    opportunities = data.get('opportunities', [])
    
    # Check for alerts
    holder_spikes = check_holder_spikes(opportunities, threshold=15)
    volume_spikes = check_volume_spikes(opportunities, threshold=2.0)
    concentration_warnings = check_holder_concentration(opportunities, top_holder_threshold=30)
    
    all_alerts = holder_spikes + volume_spikes + concentration_warnings
    
    # Save alerts
    Path('data').mkdir(exist_ok=True)
    
    output = {
        'timestamp': datetime.utcnow().isoformat(),
        'total_alerts': len(all_alerts),
        'holder_spikes': len(holder_spikes),
        'volume_spikes': len(volume_spikes),
        'concentration_warnings': len(concentration_warnings),
        'alerts': all_alerts
    }
    
    with open('data/alerts.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    # Summary
    print(f"\n📊 Alert Summary:")
    print(f"  👥 Holder Spikes: {len(holder_spikes)}")
    print(f"  📊 Volume Spikes: {len(volume_spikes)}")
    print(f"  ⚠️ Concentration: {len(concentration_warnings)}")
    print(f"  Total: {len(all_alerts)}")
    
    if all_alerts:
        print(f"\n🔥 Top Alerts:")
        for alert in all_alerts[:5]:
            if alert['type'] == 'HOLDER_SPIKE':
                print(f"  👥 {alert['symbol']}: +{alert['holder_growth']:.1f}% holders")
            elif alert['type'] == 'VOLUME_SPIKE':
                print(f"  📊 {alert['symbol']}: {alert['vol_ratio']:.1f}x vol ratio")
            elif alert['type'] == 'HOLDER_CONCENTRATION':
                print(f"  ⚠️ {alert['symbol']}: {alert['top_holder_pct']:.1f}% top holder")
    
    # Send Telegram alerts if configured
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if bot_token and chat_id and all_alerts:
        print(f"\n📱 Sending {len(all_alerts)} Telegram alerts...")
        for alert in all_alerts:
            if send_telegram_alert(alert, bot_token, chat_id):
                print(f"  ✓ {alert['symbol']}")
            else:
                print(f"  ✗ {alert['symbol']} (failed)")

if __name__ == "__main__":
    main()
