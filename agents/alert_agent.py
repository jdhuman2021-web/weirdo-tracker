"""
Alert Agent v1.0
Checks thresholds and sends notifications
"""

import json
import os
from datetime import datetime

def check_alerts():
    """Check for alert conditions"""
    print("🚨 Alert Agent v1.0 - Checking thresholds...")
    
    # Read opportunities
    try:
        with open('data/opportunities.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ No opportunities data found.")
        return
    
    opportunities = data.get('opportunities', [])
    alerts = []
    
    for opp in opportunities:
        # Check conditions
        if opp['score'] >= 80:
            alerts.append({
                'type': 'STRONG_BUY',
                'symbol': opp['symbol'],
                'message': f"{opp['symbol']} scored {opp['score']}/100 - STRONG BUY signal",
                'timestamp': datetime.utcnow().isoformat()
            })
        
        if opp.get('price_change_1h', 0) < -30:
            alerts.append({
                'type': 'PRICE_DROP',
                'symbol': opp['symbol'],
                'message': f"{opp['symbol']} dropped {abs(opp['price_change_1h']):.1f}% in 1h",
                'timestamp': datetime.utcnow().isoformat()
            })
    
    # Save alerts
    if alerts:
        with open('data/alerts.json', 'w') as f:
            json.dump({
                'timestamp': datetime.utcnow().isoformat(),
                'alert_count': len(alerts),
                'alerts': alerts
            }, f, indent=2)
        
        print(f"\n🔔 {len(alerts)} ALERTS TRIGGERED:")
        for alert in alerts:
            print(f"  [{alert['type']}] {alert['message']}")
        
        # In production, send Telegram here
        # send_telegram_alert(alerts)
    else:
        print("\n✅ No alerts - all quiet")

def send_telegram_alert(alerts):
    """Send Telegram notification (placeholder)"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("⚠️  Telegram credentials not configured")
        return
    
    # Implementation would go here
    print("📱 Would send Telegram alert")

if __name__ == "__main__":
    check_alerts()
