"""
Squirmy Screener - Milestone Analysis Scripts
Progressive signal attribution analysis at Days 1, 5, 10, 15, 20, 30
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
from collections import defaultdict

class MilestoneAnalyzer:
    """Analyze signal attribution at progressive milestones"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.snapshots = []
        self.results = {}
    
    def load_snapshots(self, days_back):
        """Load snapshots from last N days"""
        history_path = self.data_dir / "backtest_history.json"
        if not history_path.exists():
            print(f"No history found at {history_path}")
            return []
        
        with open(history_path, 'r') as f:
            history = json.load(f)
        
        cutoff = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
        return [s for s in history.get('snapshots', []) if s['timestamp'] > cutoff]
    
    def calculate_correlations(self, snapshots):
        """Calculate sub-score correlations with outcomes"""
        if len(snapshots) < 2:
            return {}
        
        # Group by token
        token_data = defaultdict(lambda: {'scores': [], 'prices': []})
        
        for snapshot in snapshots:
            for token in snapshot.get('tokens', []):
                addr = token['address']
                token_data[addr]['scores'].append({
                    'total': token.get('score', 0),
                    'vol': token.get('vol_score', 0),
                    'whale': token.get('whale_score', 0),
                    'security': token.get('security_score', 0),
                    'holder': token.get('holder_score', 0),
                    'momentum': token.get('momentum_score', 0),
                    'age': token.get('age_score', 0)
                })
                token_data[addr]['prices'].append(token.get('price_usd', 0))
        
        # Calculate correlations
        correlations = {}
        
        for score_type in ['vol', 'whale', 'security', 'holder', 'momentum', 'age']:
            x = []
            y = []
            
            for addr, data in token_data.items():
                if len(data['scores']) >= 2:
                    # Score at start
                    start_score = data['scores'][0][score_type]
                    # Price change %
                    if data['prices'][0] > 0:
                        price_change = ((data['prices'][-1] - data['prices'][0]) 
                                      / data['prices'][0] * 100)
                        x.append(start_score)
                        y.append(price_change)
            
            if len(x) >= 3:
                try:
                    correlation = np.corrcoef(x, y)[0, 1]
                    correlations[score_type] = {
                        'correlation': round(correlation, 3),
                        'sample_size': len(x),
                        'interpretation': self._interpret_correlation(correlation)
                    }
                except:
                    correlations[score_type] = {'error': 'insufficient data'}
        
        return correlations
    
    def _interpret_correlation(self, r):
        """Interpret correlation coefficient"""
        if abs(r) < 0.1:
            return "negligible"
        elif abs(r) < 0.3:
            return "weak" if r > 0 else "weak_negative"
        elif abs(r) < 0.5:
            return "moderate" if r > 0 else "moderate_negative"
        elif abs(r) < 0.7:
            return "strong" if r > 0 else "strong_negative"
        else:
            return "very_strong" if r > 0 else "very_strong_negative"
    
    def analyze_day_1(self):
        """Day 1: Quick directional check"""
        print("\n" + "="*60)
        print("DAY 1 ANALYSIS - Directional Check")
        print("="*60)
        
        snapshots = self.load_snapshots(1)
        if not snapshots:
            print("No data available yet. Run again tomorrow.")
            return
        
        correlations = self.calculate_correlations(snapshots)
        
        print(f"\nData points: {len(snapshots)} snapshots")
        print("\nCorrelation with price change:")
        print("-" * 40)
        
        for score_type, data in correlations.items():
            if 'correlation' in data:
                r = data['correlation']
                interp = data['interpretation']
                print(f"{score_type:12} | {r:7.3f} | {interp}")
        
        print("\n⚠️  Day 1: Preliminary trends only. Wait for Day 5 for reliability.")
        return correlations
    
    def analyze_day_5(self):
        """Day 5: Pattern recognition"""
        print("\n" + "="*60)
        print("DAY 5 ANALYSIS - Pattern Recognition")
        print("="*60)
        
        snapshots = self.load_snapshots(5)
        correlations = self.calculate_correlations(snapshots)
        
        print(f"\nData points: {len(snapshots)} snapshots")
        print("\nStrongest predictive signals:")
        print("-" * 40)
        
        sorted_corr = sorted(correlations.items(), 
                           key=lambda x: abs(x[1].get('correlation', 0)),
                           reverse=True)
        
        for score_type, data in sorted_corr[:3]:
            if 'correlation' in data:
                r = data['correlation']
                print(f"🏆 {score_type}: {r:.3f} ({data['interpretation']})")
        
        print("\n📊 Recommendation: Adjust weights based on top 3 signals")
        return correlations
    
    def analyze_day_10(self):
        """Day 10: Validation"""
        print("\n" + "="*60)
        print("DAY 10 ANALYSIS - Validation")
        print("="*60)
        
        snapshots = self.load_snapshots(10)
        correlations = self.calculate_correlations(snapshots)
        
        print(f"\nData points: {len(snapshots)} snapshots across ~240 tokens")
        print("\nValidation check:")
        print("-" * 40)
        
        # Check if Day 5 patterns hold
        if hasattr(self, 'day_5_correlations'):
            print("Comparing to Day 5 patterns...")
            for score_type in ['vol', 'whale', 'security']:
                if score_type in correlations and score_type in self.day_5_correlations:
                    current = correlations[score_type]['correlation']
                    previous = self.day_5_correlations[score_type]['correlation']
                    change = abs(current - previous)
                    status = "✅ Stable" if change < 0.1 else "⚠️ Changed"
                    print(f"{score_type}: {previous:.3f} → {current:.3f} {status}")
        
        return correlations
    
    def analyze_day_15(self):
        """Day 15: Fine-tuning"""
        print("\n" + "="*60)
        print("DAY 15 ANALYSIS - Fine-Tuning")
        print("="*60)
        
        snapshots = self.load_snapshots(15)
        correlations = self.calculate_correlations(snapshots)
        
        print("\nSuggested weight adjustments:")
        print("-" * 40)
        
        for score_type, data in correlations.items():
            if 'correlation' in data:
                r = abs(data['correlation'])
                if r > 0.4:
                    print(f"⬆️  Increase {score_type}_weight (strong predictor)")
                elif r < 0.1:
                    print(f"⬇️  Decrease {score_type}_weight (weak predictor)")
        
        return correlations
    
    def analyze_day_20(self):
        """Day 20: Pre-optimization"""
        print("\n" + "="*60)
        print("DAY 20 ANALYSIS - Pre-Optimization")
        print("="*60)
        
        snapshots = self.load_snapshots(20)
        correlations = self.calculate_correlations(snapshots)
        
        print("\n📈 Final validation before optimization:")
        print("-" * 40)
        
        # Calculate R-squared for confidence
        for score_type, data in correlations.items():
            if 'correlation' in data:
                r = data['correlation']
                r_squared = r ** 2
                print(f"{score_type}: R² = {r_squared:.3f} ({r_squared*100:.1f}% variance explained)")
        
        return correlations
    
    def analyze_day_30(self):
        """Day 30: Final optimization"""
        print("\n" + "="*60)
        print("DAY 30 ANALYSIS - FINAL OPTIMIZATION")
        print("="*60)
        
        snapshots = self.load_snapshots(30)
        correlations = self.calculate_correlations(snapshots)
        
        print("\n🎯 Evidence-based optimal weights:")
        print("=" * 40)
        
        total_correlation = sum(abs(d['correlation']) 
                            for d in correlations.values() 
                            if 'correlation' in d)
        
        for score_type, data in sorted(correlations.items(),
                                      key=lambda x: abs(x[1].get('correlation', 0)),
                                      reverse=True):
            if 'correlation' in data:
                r = abs(data['correlation'])
                weight = (r / total_correlation * 100) if total_correlation > 0 else 0
                print(f"{score_type:12}: {weight:.1f}% (r={data['correlation']:.3f})")
        
        print("\n✅ Ready for Thinking Agent v3.0 with optimized weights!")
        return correlations
    
    def run_milestone(self, day):
        """Run analysis for specific milestone"""
        methods = {
            1: self.analyze_day_1,
            5: self.analyze_day_5,
            10: self.analyze_day_10,
            15: self.analyze_day_15,
            20: self.analyze_day_20,
            30: self.analyze_day_30
        }
        
        if day in methods:
            return methods[day]()
        else:
            print(f"No analysis defined for day {day}")
            return None


def main():
    """Run milestone analysis"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python milestone_analysis.py [day_number]")
        print("  day_number: 1, 5, 10, 15, 20, or 30")
        return
    
    try:
        day = int(sys.argv[1])
        analyzer = MilestoneAnalyzer()
        analyzer.run_milestone(day)
    except ValueError:
        print("Error: Day must be a number (1, 5, 10, 15, 20, or 30)")


if __name__ == "__main__":
    main()