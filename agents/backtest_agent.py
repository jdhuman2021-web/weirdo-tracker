"""
Backtesting Agent v1.0
Track scoring accuracy over time and measure predictions vs reality

This agent:
1. Records current scores and prices
2. Waits 24h/7d to measure actual performance
3. Calculates if high-score tokens outperformed low-score tokens
4. Reports accuracy metrics

Usage:
    python agents/backtest_agent.py
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

def load_current_opportunities():
    """Load current opportunities from JSON"""
    try:
        with open('data/opportunities.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("ERROR: No opportunities.json found. Run thinking_agent.py first.")
        return None

def load_historical_snapshots():
    """Load historical price snapshots"""
    try:
        with open('data/backtest_history.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"snapshots": []}

def save_snapshot(opportunities):
    """Save current state for future backtesting"""
    history = load_historical_snapshots()
    
    snapshot = {
        "timestamp": datetime.utcnow().isoformat(),
        "tokens": []
    }
    
    for opp in opportunities.get('opportunities', []):
        snapshot["tokens"].append({
            "symbol": opp.get("symbol"),
            "address": opp.get("address"),
            "score": opp.get("score"),
            "signal": opp.get("signal"),
            "price_usd": opp.get("price_usd"),
            "market_cap": opp.get("market_cap"),
            "volume_24h": opp.get("volume_24h"),
            "liquidity_usd": opp.get("liquidity_usd"),
            "price_change_24h": opp.get("price_change_24h"),
            "price_change_1h": opp.get("price_change_1h"),
            "reasons": opp.get("reasons", []),
            "risk_factors": opp.get("risk_factors", []),
            # NEW: SolanaTracker data
            "security_score": opp.get("security_score"),
            "holder_count": opp.get("holder_count"),
            "lp_burn": opp.get("lp_burn"),
            "buy_sell_ratio": opp.get("buy_sell_ratio"),
            "age_days": opp.get("age_days"),
            "socials": opp.get("socials", {})
        })
    
    history["snapshots"].append(snapshot)
    
    # Keep only last 30 days
    cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()
    history["snapshots"] = [s for s in history["snapshots"] if s["timestamp"] > cutoff]
    
    with open('data/backtest_history.json', 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2)
    
    return snapshot

def calculate_performance(current, previous):
    """Calculate price performance between two snapshots"""
    results = []
    
    # Create lookup by address
    prev_lookup = {t["address"]: t for t in previous.get("tokens", [])}
    
    for token in current.get("tokens", []):
        address = token.get("address")
        if address in prev_lookup:
            prev_token = prev_lookup[address]
            
            # Calculate price change
            prev_price = prev_token.get("price_usd", 0)
            curr_price = token.get("price_usd", 0)
            
            if prev_price > 0:
                price_change_pct = ((curr_price - prev_price) / prev_price) * 100
            else:
                price_change_pct = 0
            
            results.append({
                "symbol": token.get("symbol"),
                "address": address,
                "score": prev_token.get("score"),
                "signal": prev_token.get("signal"),
                "prev_price": prev_price,
                "curr_price": curr_price,
                "price_change_pct": price_change_pct,
                "hours_elapsed": 24  # Assuming daily snapshots
            })
    
    return results

def analyze_accuracy(results):
    """Analyze if high scores predicted good performance"""
    if not results:
        return None
    
    # Group by signal
    by_signal = {}
    for r in results:
        signal = r.get("signal", "UNKNOWN")
        if signal not in by_signal:
            by_signal[signal] = []
        by_signal[signal].append(r)
    
    # Calculate average performance by signal
    signal_performance = {}
    for signal, tokens in by_signal.items():
        avg_change = sum(t["price_change_pct"] for t in tokens) / len(tokens)
        positive_pct = sum(1 for t in tokens if t["price_change_pct"] > 0) / len(tokens) * 100
        
        signal_performance[signal] = {
            "count": len(tokens),
            "avg_change": round(avg_change, 2),
            "positive_pct": round(positive_pct, 1)
        }
    
    # Calculate score correlation
    # Higher scores should correlate with positive returns
    score_buckets = {
        "85+": [],  # STRONG_BUY
        "70-84": [],  # BUY
        "55-69": [],  # SPECULATIVE
        "40-54": [],  # WATCH
        "<40": []  # AVOID
    }
    
    for r in results:
        score = r.get("score", 0)
        if score >= 85:
            score_buckets["85+"].append(r)
        elif score >= 70:
            score_buckets["70-84"].append(r)
        elif score >= 55:
            score_buckets["55-69"].append(r)
        elif score >= 40:
            score_buckets["40-54"].append(r)
        else:
            score_buckets["<40"].append(r)
    
    score_performance = {}
    for bucket, tokens in score_buckets.items():
        if tokens:
            avg_change = sum(t["price_change_pct"] for t in tokens) / len(tokens)
            positive_pct = sum(1 for t in tokens if t["price_change_pct"] > 0) / len(tokens) * 100
            score_performance[bucket] = {
                "count": len(tokens),
                "avg_change": round(avg_change, 2),
                "positive_pct": round(positive_pct, 1)
            }
    
    return {
        "by_signal": signal_performance,
        "by_score": score_performance,
        "total_tokens": len(results)
    }

def generate_report(analysis, hours_elapsed=24):
    """Generate human-readable backtest report"""
    if not analysis:
        return "No data to analyze"
    
    report = []
    report.append("=" * 60)
    report.append(f"BACKTEST REPORT - {hours_elapsed}h Performance")
    report.append("=" * 60)
    report.append("")
    
    # By Signal
    report.append("PERFORMANCE BY SIGNAL:")
    report.append("-" * 40)
    report.append(f"{'Signal':<15} {'Count':>6} {'Avg %':>10} {'Positive':>10}")
    report.append("-" * 40)
    
    for signal in ["STRONG_BUY", "BUY", "SPECULATIVE", "WATCH", "AVOID"]:
        if signal in analysis["by_signal"]:
            data = analysis["by_signal"][signal]
            report.append(f"{signal:<15} {data['count']:>6} {data['avg_change']:>9.2f}% {data['positive_pct']:>9.1f}%")
    
    report.append("")
    
    # By Score
    report.append("PERFORMANCE BY SCORE:")
    report.append("-" * 40)
    report.append(f"{'Score Range':<15} {'Count':>6} {'Avg %':>10} {'Positive':>10}")
    report.append("-" * 40)
    
    for bucket in ["85+", "70-84", "55-69", "40-54", "<40"]:
        if bucket in analysis["by_score"]:
            data = analysis["by_score"][bucket]
            report.append(f"{bucket:<15} {data['count']:>6} {data['avg_change']:>9.2f}% {data['positive_pct']:>9.1f}%")
    
    report.append("")
    
    # Accuracy Assessment
    report.append("ACCURACY ASSESSMENT:")
    report.append("-" * 40)
    
    # Check if higher scores = better performance
    score_perf = analysis["by_score"]
    
    if "85+" in score_perf and "<40" in score_perf:
        high_score_avg = score_perf.get("85+", {}).get("avg_change", 0)
        low_score_avg = score_perf.get("<40", {}).get("avg_change", 0)
        
        if high_score_avg > low_score_avg:
            report.append(f"[OK] Higher scores performed better: +{high_score_avg:.1f}% vs {low_score_avg:.1f}%")
        else:
            report.append(f"[X] Lower scores performed better: {low_score_avg:.1f}% vs {high_score_avg:.1f}%")
    
    # Check BUY vs AVOID
    buy_avg = analysis["by_signal"].get("BUY", {}).get("avg_change", 0)
    avoid_avg = analysis["by_signal"].get("AVOID", {}).get("avg_change", 0)
    
    if buy_avg > avoid_avg:
        report.append(f"[OK] BUY signal outperformed AVOID: +{buy_avg:.1f}% vs {avoid_avg:.1f}%")
    else:
        report.append(f"[X] AVOID outperformed BUY: {avoid_avg:.1f}% vs {buy_avg:.1f}%")
    
    report.append("")
    report.append(f"Total tokens analyzed: {analysis['total_tokens']}")
    
    return "\n".join(report)

def main():
    """Main backtest execution"""
    print("Backtesting Agent v1.0")
    print("=" * 60)
    
    # Load current data
    current = load_current_opportunities()
    if not current:
        return
    
    # Save snapshot for future backtesting
    snapshot = save_snapshot(current)
    print(f"[OK] Saved snapshot with {len(snapshot['tokens'])} tokens")
    
    # Load history
    history = load_historical_snapshots()
    snapshots = history.get("snapshots", [])
    
    print(f"[INFO] Total snapshots: {len(snapshots)}")
    
    # Find snapshots from 24h ago
    now = datetime.utcnow()
    cutoff_24h = (now - timedelta(hours=24)).isoformat()
    cutoff_7d = (now - timedelta(days=7)).isoformat()
    
    snapshot_24h = None
    snapshot_7d = None
    
    for s in reversed(snapshots):
        if s["timestamp"] < cutoff_24h and not snapshot_24h:
            snapshot_24h = s
        if s["timestamp"] < cutoff_7d and not snapshot_7d:
            snapshot_7d = s
    
    # 24h backtest
    if snapshot_24h:
        print("\n[INFO] Running 24h backtest...")
        results_24h = calculate_performance(current, snapshot_24h)
        analysis_24h = analyze_accuracy(results_24h)
        report_24h = generate_report(analysis_24h, hours_elapsed=24)
        print(report_24h)
    else:
        print("\n[WAIT] No 24h snapshot available yet")
        print("   Backtesting will be available after 24 hours of data collection")
    
    # 7d backtest
    if snapshot_7d:
        print("\n[INFO] Running 7-day backtest...")
        results_7d = calculate_performance(current, snapshot_7d)
        analysis_7d = analyze_accuracy(results_7d)
        report_7d = generate_report(analysis_7d, hours_elapsed=168)
        print(report_7d)
    else:
        print("\n[WAIT] No 7-day snapshot available yet")
    
    # Save backtest results
    backtest_results = {
        "timestamp": now.isoformat(),
        "snapshot_count": len(snapshots),
        "has_24h_data": snapshot_24h is not None,
        "has_7d_data": snapshot_7d is not None
    }
    
    if snapshot_24h:
        backtest_results["24h_analysis"] = analysis_24h
    
    if snapshot_7d:
        backtest_results["7d_analysis"] = analysis_7d
    
    with open('data/backtest_results.json', 'w', encoding='utf-8') as f:
        json.dump(backtest_results, f, indent=2)
    
    print("\n[OK] Backtest complete. Results saved to data/backtest_results.json")

if __name__ == "__main__":
    main()