#!/usr/bin/env python3
"""
Check if any contracts breach alert thresholds.
"""

import json
import sys
from datetime import datetime

def check_alerts(tracker_data):
    """Check all contracts against thresholds and return alerts."""
    
    alerts = []
    thresholds = tracker_data.get("alert_thresholds", {})
    
    for contract in tracker_data.get("tracked_contracts", []):
        if contract.get("status") != "active":
            continue
        
        initial = contract.get("initial_data", {})
        history = contract.get("history", [])
        
        if not history:
            continue
        
        latest = history[-1]
        
        # Check price change 1h
        price_change_1h = latest.get("price_change_1h", 0)
        if abs(price_change_1h) >= thresholds.get("price_change_1h", 20):
            alerts.append({
                "contract": contract["address"],
                "symbol": contract["symbol"],
                "metric": "price_change_1h",
                "value": price_change_1h,
                "severity": "high" if abs(price_change_1h) >= 50 else "medium"
            })
        
        # Check price change 24h
        price_change_24h = latest.get("price_change_24h", 0)
        if abs(price_change_24h) >= thresholds.get("price_change_24h", 50):
            alerts.append({
                "contract": contract["address"],
                "symbol": contract["symbol"],
                "metric": "price_change_24h",
                "value": price_change_24h,
                "severity": "high"
            })
        
        # Check volume spike
        current_vol = latest.get("volume_24h", 0)
        avg_vol = sum(h.get("volume_24h", 0) for h in history[-7:]) / min(len(history), 7)
        if avg_vol > 0 and current_vol >= avg_vol * thresholds.get("volume_spike_multiplier", 2.0):
            alerts.append({
                "contract": contract["address"],
                "symbol": contract["symbol"],
                "metric": "volume_spike",
                "value": f"{current_vol/avg_vol:.1f}x",
                "severity": "medium"
            })
        
        # Check liquidity drain
        current_liq = latest.get("liquidity", 0)
        initial_liq = initial.get("liquidity", 0)
        if initial_liq > 0 and current_liq < initial_liq * 0.7:
            drain_pct = (1 - current_liq / initial_liq) * 100
            alerts.append({
                "contract": contract["address"],
                "symbol": contract["symbol"],
                "metric": "liquidity_drain",
                "value": f"-{drain_pct:.1f}%",
                "severity": "high"
            })
    
    return alerts

def main():
    if len(sys.argv) < 2:
        print("Usage: check_alerts.py <tracker_json_path>")
        sys.exit(1)
    
    tracker_path = sys.argv[1]
    
    try:
        with open(tracker_path, 'r') as f:
            tracker_data = json.load(f)
    except Exception as e:
        print(json.dumps({"error": f"Failed to load tracker: {str(e)}"}))
        sys.exit(1)
    
    alerts = check_alerts(tracker_data)
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "alert_count": len(alerts),
        "alerts": alerts
    }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()