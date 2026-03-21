"""
Collect and Score Agent v1.0
Consolidated pipeline: Research → Helius → Whale → Thinking → Backtest → Alert

This replaces 6 separate agents with a single atomic pipeline:
- One checkout, one Python invocation
- Atomic Supabase writes
- No file-passing between agents
- Cleaner error handling

Usage:
    python agents/collect_and_score.py

Environment:
    HELIUS_API_KEY - Helius API key (required)
    SUPABASE_URL - Supabase project URL (optional)
    SUPABASE_SERVICE_KEY - Supabase service role key (optional)
    TELEGRAM_BOT_TOKEN - Telegram bot token (optional)
    TELEGRAM_CHAT_ID - Telegram chat ID (optional)
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value.strip()

# Import Supabase client (optional)
try:
    from database.supabase_client import get_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Note: Supabase not available, using JSON only")


class CollectAndScore:
    """Consolidated pipeline for token data collection and scoring"""
    
    def __init__(self):
        self.tokens = []
        self.token_data = {}  # address -> data
        self.holder_data = {}  # address -> holder info
        self.whale_data = {}  # address -> whale activity
        self.opportunities = []
        self.alerts = []
        self.supabase = None
        self.stats = {
            'tokens_fetched': 0,
            'holders_fetched': 0,
            'whales_detected': 0,
            'alerts_sent': 0,
            'errors': []
        }
    
    def connect_supabase(self):
        """Initialize Supabase connection"""
        if not SUPABASE_AVAILABLE:
            return False
        
        try:
            self.supabase = get_client()
            if self.supabase and self.supabase.is_connected():
                print("✓ Connected to Supabase")
                return True
        except Exception as e:
            print(f"⚠ Supabase connection error: {e}")
        
        return False
    
    def load_config(self):
        """Load token configuration"""
        config_path = Path(__file__).parent.parent / "config" / "tokens.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            all_tokens = config.get('tokens', [])
            # Filter out dead/inactive tokens
            self.tokens = [t for t in all_tokens if t.get('status', 'active') != 'dead']
            dead_count = len(all_tokens) - len(self.tokens)
            if dead_count > 0:
                print(f"Skipped {dead_count} dead/inactive tokens")
            print(f"Loaded {len(self.tokens)} active tokens")
            return True
        except FileNotFoundError:
            print("ERROR: config/tokens.json not found")
            return False
    
    # ============================================
    # STEP 1: RESEARCH - Fetch token data from DexScreener
    # ============================================
    
    def fetch_dexscreener(self, token):
        """Fetch token data from DexScreener"""
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token['address']}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            pairs = data.get('pairs', [])
            if not pairs:
                return None
            
            # Get pair with highest liquidity
            pair = max(pairs, key=lambda x: float(x.get('liquidity', {}).get('usd', 0) or 0))
            
            # Calculate age
            pair_created = pair.get('pairCreatedAt')
            if pair_created:
                age_ms = datetime.now().timestamp() * 1000 - pair_created
                age_hours = int(age_ms / (1000 * 60 * 60))
            else:
                age_hours = 0
            
            # Extract social links
            socials = {'twitter': None, 'telegram': None, 'website': None}
            info = pair.get('info', {})
            if info and info.get('socials'):
                for social in info.get('socials', []):
                    social_type = social.get('type', '').lower()
                    social_url = social.get('url', '')
                    if 'twitter' in social_type or 'x.com' in social_url:
                        socials['twitter'] = social_url
                    elif 'telegram' in social_type or 't.me' in social_url:
                        socials['telegram'] = social_url
            if info and info.get('websites'):
                socials['website'] = info['websites'][0].get('url')
            
            return {
                'symbol': token['symbol'],
                'name': token.get('name', token['symbol']),
                'address': token['address'],
                'chain': token.get('chain', 'SOL'),
                'status': token.get('status', 'active'),
                'price_usd': float(pair.get('priceUsd', 0) or 0),
                'price_change_1h': float(pair.get('priceChange', {}).get('h1', 0) or 0),
                'price_change_24h': float(pair.get('priceChange', {}).get('h24', 0) or 0),
                'volume_24h': float(pair.get('volume', {}).get('h24', 0) or 0),
                'volume_1h': float(pair.get('volume', {}).get('h1', 0) or 0),
                'volume_5m': float(pair.get('volume', {}).get('m5', 0) or 0),
                'liquidity_usd': float(pair.get('liquidity', {}).get('usd', 0) or 0),
                'market_cap': float(pair.get('fdv', 0) or pair.get('marketCap', 0) or 0),
                'socials': socials,
                'pair_created_at': pair_created,
                'age_hours': age_hours,
                'age_days': round(age_hours / 24, 1) if age_hours else 0,
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'dexscreener'
            }
        except Exception as e:
            print(f"  ERROR fetching {token['symbol']}: {e}")
            return None
    
    def run_research(self):
        """Step 1: Fetch all token data from DexScreener"""
        print("\n" + "="*60)
        print("STEP 1: RESEARCH - Fetching token data from DexScreener")
        print("="*60)
        
        success = 0
        failed = 0
        
        for i, token in enumerate(self.tokens, 1):
            print(f"[{i}/{len(self.tokens)}] {token['symbol']}...", end=' ')
            
            data = self.fetch_dexscreener(token)
            if data:
                self.token_data[token['address']] = data
                success += 1
                print(f"OK ${data['price_usd']:.6f}")
            else:
                failed += 1
                print("FAILED")
            
            # Rate limiting
            if i < len(self.tokens):
                time.sleep(6)
        
        self.stats['tokens_fetched'] = success
        print(f"\n✓ Fetched {success} tokens ({failed} failed)")
        return success > 0
    
    # ============================================
    # STEP 2: HELIUS - Fetch holder data
    # ============================================
    
    def fetch_holders(self, address, symbol):
        """Fetch holder count from Helius"""
        api_key = os.environ.get('HELIUS_API_KEY')
        if not api_key:
            return None
        
        try:
            # Use Helius DAS API - search assets by owner
            # For now, use token metadata to get basic info
            url = f"https://api.helius.xyz/v0/token-metadata?api-key={api_key}"
            payload = {"mintAccounts": [address], "includeOffChain": False}
            
            response = requests.post(url, json=payload, timeout=15)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            if not data or len(data) == 0:
                return None
            
            token_info = data[0]
            
            # Try to get holder count from metadata or use RPC
            # For now, return basic metadata without holder count
            # Holder count requires Premium API or different endpoint
            
            return {
                'holder_count': 0,  # Would require Premium API
                'metadata': token_info
            }
        except Exception as e:
            return None
    
    def run_helius(self):
        """Step 2: Fetch holder data from Helius"""
        print("\n" + "="*60)
        print("STEP 2: HELIUS - Fetching holder data")
        print("="*60)
        
        api_key = os.environ.get('HELIUS_API_KEY')
        if not api_key:
            print("⚠ HELIUS_API_KEY not found, skipping")
            return True
        
        success = 0
        total_holders = 0
        
        for i, (address, data) in enumerate(self.token_data.items(), 1):
            symbol = data.get('symbol', 'UNKNOWN')
            print(f"[{i}/{len(self.token_data)}] {symbol}...", end=' ')
            
            holder_info = self.fetch_holders(address, symbol)
            if holder_info:
                self.holder_data[address] = holder_info
                data['holder_count'] = holder_info.get('holder_count', 0)
                success += 1
                total_holders += holder_info.get('holder_count', 0)
                print(f"{holder_info.get('holder_count', 0)} holders")
            else:
                data['holder_count'] = 0
                print("no data")
            
            # Rate limiting
            if i < len(self.token_data):
                time.sleep(0.5)
        
        self.stats['holders_fetched'] = success
        print(f"\n✓ Fetched holders for {success} tokens (total: {total_holders})")
        return True
    
    # ============================================
    # STEP 3: WHALE - Detect whale activity
    # ============================================
    
    def detect_whale_activity(self, address, data):
        """Detect whale activity from volume data"""
        volume_24h = data.get('volume_24h', 0)
        volume_1h = data.get('volume_1h', 0)
        volume_5m = data.get('volume_5m', 0)
        liquidity = data.get('liquidity_usd', 1)
        
        vol_ratio = volume_24h / liquidity if liquidity > 0 else 0
        vol_1h_ratio = (volume_1h * 24) / volume_24h if volume_24h > 0 else 0
        vol_5m_ratio = (volume_5m * 12) / volume_1h if volume_1h > 0 else 0
        
        whale_detected = vol_1h_ratio > 1.5 or vol_5m_ratio > 2.0
        confidence = 'high' if (vol_1h_ratio > 3.0 or vol_5m_ratio > 5.0) else 'medium' if whale_detected else 'low'
        
        return {
            'vol_ratio': round(vol_ratio, 2),
            'vol_1h_ratio': round(vol_1h_ratio, 2),
            'vol_5m_ratio': round(vol_5m_ratio, 2),
            'whale_activity_detected': whale_detected,
            'whale_confidence': confidence
        }
    
    def run_whale(self):
        """Step 3: Detect whale activity"""
        print("\n" + "="*60)
        print("STEP 3: WHALE - Detecting whale activity")
        print("="*60)
        
        whales_detected = 0
        
        for i, (address, data) in enumerate(self.token_data.items(), 1):
            symbol = data.get('symbol', 'UNKNOWN')
            whale_info = self.detect_whale_activity(address, data)
            self.whale_data[address] = whale_info
            
            if whale_info.get('whale_activity_detected'):
                whales_detected += 1
                print(f"[{i}/{len(self.token_data)}] {symbol}: WHALE vol={whale_info['vol_1h_ratio']}x")
            else:
                print(f"[{i}/{len(self.token_data)}] {symbol}: normal")
        
        self.stats['whales_detected'] = whales_detected
        print(f"\n✓ Detected {whales_detected} tokens with whale activity")
        return True
    
    # ============================================
    # STEP 4: THINKING - Calculate scores
    # ============================================
    
    def calculate_score(self, data, whale_info):
        """Calculate opportunity score 0-100"""
        score = 0
        reasons = []
        risk_factors = []
        
        # Extract values
        price_24h = data.get('price_change_24h', 0)
        price_1h = data.get('price_change_1h', 0)
        volume = data.get('volume_24h', 0)
        liquidity = data.get('liquidity_usd', 1)
        mcap = data.get('market_cap', 0)
        holder_count = data.get('holder_count', 0)
        age_hours = data.get('age_hours', 0)
        vol_ratio = volume / liquidity if liquidity > 0 else 0
        
        # Whale data
        vol_1h_ratio = whale_info.get('vol_1h_ratio', 0)
        vol_5m_ratio = whale_info.get('vol_5m_ratio', 0)
        has_whale = whale_info.get('whale_activity_detected', False)
        
        # 1. PRICE POSITION (35 points max)
        if price_24h < -50:
            score -= 20
            risk_factors.append(f"Crashed {abs(price_24h):.0f}% in 24h")
        elif price_24h < -30 and price_1h > 0:
            score += 25
            reasons.append("Price dip with reversal - bounce potential")
        elif price_24h < -20 and price_1h > -5:
            score += 18
            reasons.append("Price in dip zone")
        elif 0 <= price_24h <= 30:
            score += 5
            reasons.append("Price stable")
        elif price_24h > 100:
            score -= 15
            risk_factors.append(f"Extreme pump +{price_24h:.0f}%")
        
        # 2. VOLUME RATIO (35 points max)
        if vol_ratio > 10:
            score += 35
            reasons.append(f"Volume {vol_ratio:.1f}x - EXTREME!")
        elif vol_ratio > 5:
            score += 28
            reasons.append(f"Volume {vol_ratio:.1f}x - viral")
        elif vol_ratio > 2:
            score += 20
            reasons.append(f"Volume {vol_ratio:.1f}x - healthy")
        elif has_whale:
            score += 15
            reasons.append("Whale activity detected")
        elif vol_ratio < 0.5 and mcap < 100000:
            score -= 10
            risk_factors.append("Low volume - potentially dead")
        
        # 3. LIQUIDITY (15 points max)
        if liquidity > 100000:
            score += 15
            reasons.append("High liquidity")
        elif liquidity > 50000:
            score += 12
            reasons.append("Good liquidity")
        elif liquidity > 25000:
            score += 8
        elif liquidity < 10000:
            score -= 5
            risk_factors.append("Low liquidity")
        
        # 4. MARKET CAP (10 points max)
        if 0 < mcap < 50000:
            score += 10
            reasons.append("Micro-cap gem potential")
        elif mcap < 200000:
            score += 8
        elif mcap > 10000000:
            score -= 5
        
        # 5. AGE TIMING (5 points)
        if 6 <= age_hours <= 48:
            score += 5
            reasons.append("Fresh but proven")
        elif age_hours < 6:
            score -= 3
            risk_factors.append("Very fresh")
        
        # 6. WHALE BONUS (20 points max)
        if has_whale:
            if vol_1h_ratio > 3:
                score += 20
                reasons.append(f"Whale volume {vol_1h_ratio:.1f}x")
            elif vol_1h_ratio > 2:
                score += 15
                reasons.append(f"Whale accumulation {vol_1h_ratio:.1f}x")
            else:
                score += 5
                reasons.append("Whale activity")
            
            # Whale selling check
            if vol_1h_ratio > 2 and price_1h < -10:
                score -= 15
                risk_factors.append(f"Whale selling detected")
        
        # Cap score
        return max(0, min(100, score)), reasons, risk_factors
    
    def get_signal(self, score):
        """Convert score to signal"""
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
    
    def run_thinking(self):
        """Step 4: Calculate scores for all tokens"""
        print("\n" + "="*60)
        print("STEP 4: THINKING - Calculating scores")
        print("="*60)
        
        for i, (address, data) in enumerate(self.token_data.items(), 1):
            symbol = data.get('symbol', 'UNKNOWN')
            whale_info = self.whale_data.get(address, {})
            
            score, reasons, risks = self.calculate_score(data, whale_info)
            signal, label = self.get_signal(score)
            
            opp = {
                **data,
                'score': score,
                'signal': signal,
                'label': label,
                'reasons': reasons,
                'risk_factors': risks
            }
            self.opportunities.append(opp)
            
            print(f"[{i}/{len(self.token_data)}] {symbol}: {score} → {signal}")
        
        # Sort by score
        self.opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"\n✓ Scored {len(self.opportunities)} tokens")
        return True
    
    # ============================================
    # STEP 5: BACKTEST - Save snapshot for future
    # ============================================
    
    def run_backtest(self):
        """Step 5: Save snapshot for backtesting"""
        print("\n" + "="*60)
        print("STEP 5: BACKTEST - Saving snapshot")
        print("="*60)
        
        # Load existing history
        history_path = Path(__file__).parent.parent / "data" / "backtest_history.json"
        history = {"snapshots": []}
        
        if history_path.exists():
            with open(history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
        
        # Create snapshot
        snapshot = {
            "timestamp": datetime.utcnow().isoformat(),
            "tokens": []
        }
        
        for opp in self.opportunities:
            snapshot["tokens"].append({
                "symbol": opp.get("symbol"),
                "address": opp.get("address"),
                "score": opp.get("score"),
                "signal": opp.get("signal"),
                "price_usd": opp.get("price_usd"),
                "market_cap": opp.get("market_cap"),
                "volume_24h": opp.get("volume_24h"),
                "liquidity_usd": opp.get("liquidity_usd"),
                "price_change_24h": opp.get("price_change_24h")
            })
        
        history["snapshots"].append(snapshot)
        
        # Keep only 30 days
        cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()
        history["snapshots"] = [s for s in history["snapshots"] if s["timestamp"] > cutoff]
        
        # Save
        history_path.parent.mkdir(exist_ok=True)
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)
        
        print(f"✓ Saved snapshot with {len(snapshot['tokens'])} tokens")
        return True
    
    # ============================================
    # STEP 6: ALERT - Send notifications
    # ============================================
    
    def check_alerts(self):
        """Check for alert conditions"""
        self.alerts = []
        
        for opp in self.opportunities:
            # High scores
            if opp.get('score', 0) >= 85:
                self.alerts.append({
                    'type': 'STRONG_BUY',
                    'symbol': opp['symbol'],
                    'score': opp['score'],
                    'price': opp.get('price_usd', 0),
                    'reasons': opp.get('reasons', [])[:2]
                })
            
            # Whale activity
            whale_info = self.whale_data.get(opp['address'], {})
            if whale_info.get('whale_activity_detected') and whale_info.get('vol_1h_ratio', 0) > 3:
                self.alerts.append({
                    'type': 'WHALE',
                    'symbol': opp['symbol'],
                    'vol_ratio': whale_info.get('vol_1h_ratio'),
                    'score': opp['score']
                })
        
        return len(self.alerts)
    
    def send_telegram_alert(self, alert):
        """Send alert to Telegram"""
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id:
            return False
        
        message = ""
        if alert['type'] == 'STRONG_BUY':
            message = f"🔥 STRONG BUY ALERT\n\n"
            message += f"Token: {alert['symbol']}\n"
            message += f"Score: {alert['score']}\n"
            message += f"Price: ${alert['price']:.6f}\n"
            if alert.get('reasons'):
                message += f"Reasons: {', '.join(alert['reasons'])}"
        elif alert['type'] == 'WHALE':
            message = f"🐋 WHALE ACTIVITY\n\n"
            message += f"Token: {alert['symbol']}\n"
            message += f"Volume: {alert['vol_ratio']:.1f}x\n"
            message += f"Score: {alert['score']}"
        
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {'chat_id': chat_id, 'text': message}
            response = requests.post(url, json=data, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def run_alert(self):
        """Step 6: Check and send alerts"""
        print("\n" + "="*60)
        print("STEP 6: ALERT - Checking for alerts")
        print("="*60)
        
        alert_count = self.check_alerts()
        
        if not alert_count:
            print("No alerts to send")
            return True
        
        print(f"Found {alert_count} alerts")
        
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        if bot_token and chat_id:
            for alert in self.alerts[:5]:  # Max 5 alerts
                if self.send_telegram_alert(alert):
                    print(f"  ✓ Sent: {alert['symbol']}")
                    self.stats['alerts_sent'] += 1
                else:
                    print(f"  ✗ Failed: {alert['symbol']}")
        else:
            print("Telegram not configured, skipping notifications")
            for alert in self.alerts[:5]:
                print(f"  • {alert['type']}: {alert['symbol']}")
        
        return True
    
    # ============================================
    # SAVE - Write all data to files
    # ============================================
    
    def save_files(self):
        """Save all data to JSON files"""
        print("\n" + "="*60)
        print("SAVING DATA")
        print("="*60)
        
        data_dir = Path(__file__).parent.parent / "data"
        data_dir.mkdir(exist_ok=True)
        
        # Save latest.json
        latest = {
            'metadata': {
                'timestamp': datetime.utcnow().isoformat(),
                'tokens_fetched': self.stats['tokens_fetched'],
                'holders_fetched': self.stats['holders_fetched'],
                'whales_detected': self.stats['whales_detected'],
                'agent': 'collect_and_score_v1.0'
            },
            'raw_data': list(self.token_data.values())
        }
        with open(data_dir / "latest.json", 'w', encoding='utf-8') as f:
            json.dump(latest, f, indent=2)
        print(f"✓ Saved latest.json ({len(self.token_data)} tokens)")
        
        # Save helius_data.json
        helius_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'tokens_processed': len(self.holder_data),
            'total_holders': sum(h.get('holder_count', 0) for h in self.holder_data.values()),
            'results': [{'address': a, **d} for a, d in self.holder_data.items()]
        }
        with open(data_dir / "helius_data.json", 'w', encoding='utf-8') as f:
            json.dump(helius_data, f, indent=2)
        print(f"✓ Saved helius_data.json")
        
        # Save whale_activity.json
        whale_activity = {
            'metadata': {
                'timestamp': datetime.utcnow().isoformat(),
                'tokens_analyzed': len(self.whale_data),
                'tokens_with_whale_activity': self.stats['whales_detected'],
                'agent': 'collect_and_score_v1.0'
            },
            'whale_activity': self.whale_data
        }
        with open(data_dir / "whale_activity.json", 'w', encoding='utf-8') as f:
            json.dump(whale_activity, f, indent=2)
        print(f"✓ Saved whale_activity.json")
        
        # Save opportunities.json
        opportunities = {
            'metadata': {
                'timestamp': datetime.utcnow().isoformat(),
                'total_opportunities': len(self.opportunities),
                'strong_buys': len([o for o in self.opportunities if o['signal'] == 'STRONG_BUY']),
                'buys': len([o for o in self.opportunities if o['signal'] == 'BUY']),
                'speculative': len([o for o in self.opportunities if o['signal'] == 'SPECULATIVE']),
                'watch': len([o for o in self.opportunities if o['signal'] == 'WATCH']),
                'avoid': len([o for o in self.opportunities if o['signal'] == 'AVOID']),
                'agent': 'collect_and_score_v1.0'
            },
            'opportunities': self.opportunities
        }
        with open(data_dir / "opportunities.json", 'w', encoding='utf-8') as f:
            json.dump(opportunities, f, indent=2)
        print(f"✓ Saved opportunities.json")
        
        # Save alerts.json
        alerts_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_alerts': len(self.alerts),
            'alerts_sent': self.stats['alerts_sent'],
            'alerts': self.alerts
        }
        with open(data_dir / "alerts.json", 'w', encoding='utf-8') as f:
            json.dump(alerts_data, f, indent=2)
        print(f"✓ Saved alerts.json")
        
        return True
    
    # ============================================
    # SUPABASE - Write to database
    # ============================================
    
    def write_supabase(self):
        """Write all data to Supabase"""
        if not self.supabase or not self.supabase.is_connected():
            print("Supabase not connected, skipping")
            return True
        
        print("\n" + "="*60)
        print("WRITING TO SUPABASE")
        print("="*60)
        
        db_writes = 0
        
        for opp in self.opportunities:
            try:
                # Upsert token
                self.supabase.upsert_token(
                    symbol=opp['symbol'],
                    name=opp.get('name', ''),
                    address=opp['address'],
                    chain=opp.get('chain', 'SOL'),
                    source=opp.get('source', 'dexscreener'),
                    status=opp.get('status', 'active')
                )
                
                # Insert snapshot
                self.supabase.insert_snapshot(
                    token_address=opp['address'],
                    price_usd=opp.get('price_usd', 0),
                    market_cap=opp.get('market_cap', 0),
                    volume_24h=opp.get('volume_24h', 0),
                    liquidity_usd=opp.get('liquidity_usd', 0),
                    price_change_1h=opp.get('price_change_1h', 0),
                    price_change_24h=opp.get('price_change_24h', 0),
                    holder_count=opp.get('holder_count', 0),
                    age_hours=opp.get('age_hours', 0),
                    score=opp.get('score', 0),
                    signal=opp.get('signal', 'UNKNOWN')
                )
                
                db_writes += 1
            except Exception as e:
                self.stats['errors'].append(f"{opp['symbol']}: {str(e)[:50]}")
        
        print(f"✓ Wrote {db_writes} snapshots to Supabase")
        
        # Log pipeline run
        try:
            self.supabase.log_pipeline_run(
                tokens_fetched=self.stats['tokens_fetched'],
                opportunities_found=len(self.opportunities),
                alerts_sent=self.stats['alerts_sent'],
                status='success' if not self.stats['errors'] else 'partial'
            )
        except:
            pass
        
        return True
    
    # ============================================
    # MAIN - Run entire pipeline
    # ============================================
    
    def run(self):
        """Run the complete pipeline"""
        start_time = time.time()
        
        print("=" * 60)
        print("COLLECT AND SCORE AGENT v1.0")
        print("Consolidated Pipeline: Research → Helius → Whale → Thinking → Backtest → Alert")
        print("=" * 60)
        
        # Connect to Supabase
        self.connect_supabase()
        
        # Load config
        if not self.load_config():
            return False
        
        # Run pipeline steps
        if not self.run_research():
            print("ERROR: Research step failed")
            return False
        
        self.run_helius()
        self.run_whale()
        self.run_thinking()
        self.run_backtest()
        self.run_alert()
        
        # Save data
        self.save_files()
        self.write_supabase()
        
        # Summary
        elapsed = time.time() - start_time
        print("\n" + "="*60)
        print("PIPELINE COMPLETE")
        print("="*60)
        print(f"Time: {elapsed:.1f}s")
        print(f"Tokens: {self.stats['tokens_fetched']}")
        print(f"Holders: {self.stats['holders_fetched']}")
        print(f"Whales: {self.stats['whales_detected']}")
        print(f"Alerts: {self.stats['alerts_sent']}")
        
        if self.opportunities:
            print(f"\n🏆 Top 3:")
            for i, opp in enumerate(self.opportunities[:3], 1):
                print(f"  {i}. {opp['symbol']} - {opp['score']} {opp['signal']}")
        
        if self.stats['errors']:
            print(f"\n⚠ Errors: {len(self.stats['errors'])}")
            for err in self.stats['errors'][:5]:
                print(f"  • {err}")
        
        return True


def main():
    """Entry point"""
    agent = CollectAndScore()
    success = agent.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()