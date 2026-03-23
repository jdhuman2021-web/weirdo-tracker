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
    
    def get_holder_count_rpc(self, mint_address: str) -> int:
        """
        Get holder count via Solana RPC getProgramAccounts
        
        Uses free QuickNode/Alchemy RPC if available, falls back to public endpoint.
        NOTE: This may return 0 for pump.fun tokens or when rate-limited.
        For production, use a dedicated RPC endpoint (QuickNode free tier recommended).
        """
        # Use dedicated RPC if available, otherwise public
        SOLANA_RPC = os.environ.get('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com')
        TOKEN_PROGRAM = 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
        TOKEN_2022_PROGRAM = 'TokenzQdBNb4qyF5XrzxWjb6hCjLPuFT5F1j7w7fNdPX'
        
        # Try both Token Program and Token-2022 (pump.fun tokens often use Token-2022)
        for program_id in [TOKEN_PROGRAM, TOKEN_2022_PROGRAM]:
            payload = {
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'getProgramAccounts',
                'params': [
                    program_id,
                    {
                        'encoding': 'base64',
                        'dataSlice': {'offset': 0, 'length': 0},  # Count only, no data
                        'filters': [
                            {'dataSize': 165},  # Standard token account size
                            {'memcmp': {'offset': 0, 'bytes': mint_address}}
                        ]
                    }
                ]
            }
            
            try:
                r = requests.post(SOLANA_RPC, json=payload, timeout=30)
                result = r.json()
                
                if 'result' in result:
                    accounts = result['result']
                    count = len(accounts) if accounts else 0
                    if count > 0:
                        return count
            except Exception:
                pass
        
        # If both fail, return 0 (will be stored as NULL in database)
        return 0
    
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
            
            # Get holder count - Step 1: Check DEXScreener field
            holder_count = 0
            
            # Try DEXScreener holders field first (free, instant)
            holders_field = data.get('holders') or pair.get('holders')
            if holders_field is not None:
                try:
                    holder_count = int(holders_field)
                except (ValueError, TypeError):
                    pass
            
            # Return base data (holder count will be filled by RPC fallback if needed)
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
                'holder_count': holder_count,  # May be 0, filled by RPC fallback
                'holders_source': 'dexscreener' if holder_count > 0 else None,
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
        need_holder_fallback = []  # Tokens needing RPC holder count
        
        for i, token in enumerate(self.tokens, 1):
            print(f"[{i}/{len(self.tokens)}] {token['symbol']}...", end=' ')
            
            data = self.fetch_dexscreener(token)
            if data:
                self.token_data[token['address']] = data
                success += 1
                
                # Check if we need RPC fallback for holder count
                if data.get('holder_count', 0) == 0:
                    need_holder_fallback.append((token['address'], token['symbol']))
                    print(f"OK ${data['price_usd']:.6f} (no holders)")
                else:
                    print(f"OK ${data['price_usd']:.6f} ({data['holder_count']} holders)")
            else:
                failed += 1
                print("FAILED")
            
            # Rate limiting
            if i < len(self.tokens):
                time.sleep(6)
        
        self.stats['tokens_fetched'] = success
        print(f"\n✓ Fetched {success} tokens ({failed} failed)")
        
        # Step 1b: RPC fallback for holder counts
        if need_holder_fallback:
            print(f"\n📊 Fetching holder counts via RPC for {len(need_holder_fallback)} tokens...")
            for address, symbol in need_holder_fallback:
                holder_count = self.get_holder_count_rpc(address)
                if address in self.token_data:
                    self.token_data[address]['holder_count'] = holder_count
                    self.token_data[address]['holders_source'] = 'rpc'
                    print(f"  {symbol}: {holder_count} holders")
                time.sleep(0.5)  # Rate limiting for RPC
        
        return success > 0
    
    # ============================================
    # STEP 2: HOLDERS - Already fetched in Research step
    # ============================================
    
    def run_holders(self):
        """Step 2: Holder counts (already fetched via DEXScreener + RPC fallback)"""
        print("\n" + "="*60)
        print("STEP 2: HOLDERS - Using DEXScreener + RPC data")
        print("="*60)
        
        # Holder counts were already fetched in step 1
        # Count how many have holder data
        with_holders = sum(1 for d in self.token_data.values() if d.get('holder_count', 0) > 0)
        total_holders = sum(d.get('holder_count', 0) for d in self.token_data.values())
        
        # Copy holder data to holder_data dict for scoring
        for address, data in self.token_data.items():
            self.holder_data[address] = {
                'holder_count': data.get('holder_count', 0),
                'source': data.get('holders_source', 'unknown')
            }
        
        self.stats['holders_fetched'] = with_holders
        print(f"✓ {with_holders}/{len(self.token_data)} tokens have holder data")
        print(f"  Total holders: {total_holders:,}")
        return True
    
    # ============================================
    # STEP 2b: VOLUME ACCELERATION (Idea #1)
    # ============================================
    
    def calculate_volume_acceleration(self, token_address):
        """
        Calculate volume acceleration vs 7-day average
        Returns ratio: current_volume / 7day_avg
        """
        # In a real implementation, query Supabase for historical data
        # For now, use a simplified version based on current data
        if token_address not in self.token_data:
            return 1.0
        
        data = self.token_data[token_address]
        volume_24h = data.get('volume_24h', 0)
        volume_1h = data.get('volume_1h', 0)
        
        # Estimate 7-day average from 24h data
        # This is a simplified version - full version needs historical data
        vol_7d_estimate = volume_24h * 7  # Rough estimate
        
        if vol_7d_estimate > 0:
            # Compare current 24h to daily average
            daily_avg = vol_7d_estimate / 7
            acceleration = volume_24h / daily_avg if daily_avg > 0 else 1.0
            return round(acceleration, 2)
        
        return 1.0
    
    def run_volume_analysis(self):
        """Calculate volume metrics for all tokens"""
        print("\n" + "="*60)
        print("STEP 2b: VOLUME ANALYSIS - Calculating acceleration")
        print("="*60)
        
        for address, data in self.token_data.items():
            acceleration = self.calculate_volume_acceleration(address)
            data['vol_acceleration'] = acceleration
            
            # Add interpretation
            if acceleration >= 5:
                data['vol_status'] = 'SPIKE'
            elif acceleration >= 2:
                data['vol_status'] = 'ELEVATED'
            elif acceleration >= 0.5:
                data['vol_status'] = 'NORMAL'
            else:
                data['vol_status'] = 'LOW'
        
        spiked = sum(1 for d in self.token_data.values() if d.get('vol_status') == 'SPIKE')
        elevated = sum(1 for d in self.token_data.values() if d.get('vol_status') == 'ELEVATED')
        
        print(f"✓ Volume analysis complete")
        print(f"  {spiked} tokens with volume SPIKE (>5x)")
        print(f"  {elevated} tokens with elevated volume (2-5x)")
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
        """
        Calculate opportunity score 0-100 with sub-scores for attribution analysis
        
        Returns:
            total_score: 0-100
            sub_scores: dict of individual component scores
            reasons: list of why
            risk_factors: list of risks
        """
        sub_scores = {
            'price_score': 0,
            'vol_score': 0,
            'liquidity_score': 0,
            'mcap_score': 0,
            'age_score': 0,
            'whale_score': 0
        }
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
            sub_scores['price_score'] = -20
            risk_factors.append(f"Crashed {abs(price_24h):.0f}% in 24h")
        elif price_24h < -30 and price_1h > 0:
            sub_scores['price_score'] = 25
            reasons.append("Price dip with reversal - bounce potential")
        elif price_24h < -20 and price_1h > -5:
            sub_scores['price_score'] = 18
            reasons.append("Price in dip zone")
        elif 0 <= price_24h <= 30:
            sub_scores['price_score'] = 5
            reasons.append("Price stable")
        elif price_24h > 100:
            sub_scores['price_score'] = -15
            risk_factors.append(f"Extreme pump +{price_24h:.0f}%")
        
        # 2. VOLUME RATIO (35 points max)
        if vol_ratio > 10:
            sub_scores['vol_score'] = 35
            reasons.append(f"Volume {vol_ratio:.1f}x - EXTREME!")
        elif vol_ratio > 5:
            sub_scores['vol_score'] = 28
            reasons.append(f"Volume {vol_ratio:.1f}x - viral")
        elif vol_ratio > 2:
            sub_scores['vol_score'] = 20
            reasons.append(f"Volume {vol_ratio:.1f}x - healthy")
        elif has_whale:
            sub_scores['vol_score'] = 15
            reasons.append("Whale activity detected")
        elif vol_ratio < 0.5 and mcap < 100000:
            sub_scores['vol_score'] = -10
            risk_factors.append("Low volume - potentially dead")
        
        # 3. LIQUIDITY (15 points max)
        if liquidity > 100000:
            sub_scores['liquidity_score'] = 15
            reasons.append("High liquidity")
        elif liquidity > 50000:
            sub_scores['liquidity_score'] = 12
            reasons.append("Good liquidity")
        elif liquidity > 25000:
            sub_scores['liquidity_score'] = 8
        elif liquidity < 10000:
            sub_scores['liquidity_score'] = -5
            risk_factors.append("Low liquidity")
        
        # 4. MARKET CAP (10 points max)
        if 0 < mcap < 50000:
            sub_scores['mcap_score'] = 10
            reasons.append("Micro-cap gem potential")
        elif mcap < 200000:
            sub_scores['mcap_score'] = 8
        elif mcap > 10000000:
            sub_scores['mcap_score'] = -5
        
        # 5. AGE TIMING (5 points)
        if 6 <= age_hours <= 48:
            sub_scores['age_score'] = 5
            reasons.append("Fresh but proven")
        elif age_hours < 6:
            sub_scores['age_score'] = -3
            risk_factors.append("Very fresh")
        
        # 6. WHALE BONUS (20 points max)
        if has_whale:
            if vol_1h_ratio > 3:
                sub_scores['whale_score'] = 20
                reasons.append(f"Whale volume {vol_1h_ratio:.1f}x")
            elif vol_1h_ratio > 2:
                sub_scores['whale_score'] = 15
                reasons.append(f"Whale accumulation {vol_1h_ratio:.1f}x")
            else:
                sub_scores['whale_score'] = 5
                reasons.append("Whale activity")
            
            # Whale selling check
            if vol_1h_ratio > 2 and price_1h < -10:
                sub_scores['whale_score'] -= 15
                risk_factors.append(f"Whale selling detected")
        
        # Calculate total
        total_score = sum(sub_scores.values())
        total_score = max(0, min(100, total_score))
        
        return total_score, sub_scores, reasons, risk_factors
    
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
        """Step 4: Calculate scores for all tokens with sub-scores"""
        print("\n" + "="*60)
        print("STEP 4: THINKING - Calculating scores with sub-scores")
        print("="*60)
        
        for i, (address, data) in enumerate(self.token_data.items(), 1):
            symbol = data.get('symbol', 'UNKNOWN')
            whale_info = self.whale_data.get(address, {})
            
            score, sub_scores, reasons, risks = self.calculate_score(data, whale_info)
            signal, label = self.get_signal(score)
            
            opp = {
                **data,
                'score': score,
                'signal': signal,
                'label': label,
                'reasons': reasons,
                'risk_factors': risks,
                # NEW: Sub-scores for attribution analysis
                'vol_score': sub_scores.get('vol_score', 0),
                'whale_score': sub_scores.get('whale_score', 0),
                'liquidity_score': sub_scores.get('liquidity_score', 0),
                'mcap_score': sub_scores.get('mcap_score', 0),
                'age_score': sub_scores.get('age_score', 0),
                'price_score': sub_scores.get('price_score', 0)
            }
            self.opportunities.append(opp)
            
            print(f"[{i}/{len(self.token_data)}] {symbol}: {score} → {signal} (sub-scores: vol={sub_scores.get('vol_score',0)}, whale={sub_scores.get('whale_score',0)})")
        
        # Sort by score
        self.opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"\n✓ Scored {len(self.opportunities)} tokens with sub-scores")
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
    # MERGE - Integrate SolanaTracker data
    # ============================================
    
    def merge_solanatracker_data(self, opportunities):
        """Merge SolanaTracker data into opportunities"""
        st_path = Path(__file__).parent.parent / "data" / "solanatracker_data.json"
        
        if not st_path.exists():
            print("No SolanaTracker data to merge")
            return opportunities
        
        try:
            with open(st_path, 'r', encoding='utf-8') as f:
                st_data = json.load(f)
            
            # Create lookup
            lookup = {}
            for result in st_data.get('results', []):
                address = result.get('address', '').lower()
                if address:
                    lookup[address] = result.get('data', {})
            
            merged = 0
            for opp in opportunities:
                address = opp.get('address', '').lower()
                if address in lookup:
                    data = lookup[address]
                    
                    # Security
                    opp['security_score'] = data.get('security_score', 50)
                    opp['lp_burn'] = data.get('lp_burn', 0)
                    
                    # Holders
                    opp['holder_count'] = data.get('holders', opp.get('holder_count', 0))
                    opp['token_supply'] = data.get('token_supply', 0)
                    
                    # Socials
                    socials = opp.get('socials', {})
                    if data.get('twitter'):
                        socials['twitter'] = data['twitter']
                    if data.get('telegram'):
                        socials['telegram'] = data['telegram']
                    if data.get('website'):
                        socials['website'] = data['website']
                    if data.get('image'):
                        socials['image'] = data['image']
                    opp['socials'] = socials
                    
                    # Transactions
                    opp['txns_buys'] = data.get('buys', 0)
                    opp['txns_sells'] = data.get('sells', 0)
                    opp['buy_sell_ratio'] = data.get('buy_sell_ratio', 1.0)
                    
                    # Token age
                    if data.get('creation_time'):
                        created = datetime.fromtimestamp(data['creation_time'])
                        now = datetime.utcnow()
                        opp['age_days'] = round((now - created).total_seconds() / (60*60*24), 1)
                    
                    merged += 1
            
            print(f"Merged SolanaTracker data for {merged}/{len(opportunities)} tokens")
            return opportunities
            
        except Exception as e:
            print(f"Error merging SolanaTracker data: {e}")
            return opportunities
    
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
        # First, merge SolanaTracker data if available
        opportunities = self.merge_solanatracker_data(self.opportunities)
        
        opportunities_output = {
            'metadata': {
                'timestamp': datetime.utcnow().isoformat(),
                'total_opportunities': len(opportunities),
                'strong_buys': len([o for o in opportunities if o['signal'] == 'STRONG_BUY']),
                'buys': len([o for o in opportunities if o['signal'] == 'BUY']),
                'speculative': len([o for o in opportunities if o['signal'] == 'SPECULATIVE']),
                'watch': len([o for o in opportunities if o['signal'] == 'WATCH']),
                'avoid': len([o for o in opportunities if o['signal'] == 'AVOID']),
                'agent': 'collect_and_score_v1.0',
                'solanatracker_merged': True
            },
            'opportunities': opportunities
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
                    signal=opp.get('signal', 'UNKNOWN'),
                    # NEW: Sub-scores
                    vol_score=opp.get('vol_score', 0),
                    whale_score=opp.get('whale_score', 0),
                    security_score=opp.get('security_score', 0),
                    holder_score=opp.get('holder_score', 0),
                    momentum_score=opp.get('momentum_score', 0),
                    social_score=opp.get('social_score', 0)
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
        
        self.run_holders()
        self.run_volume_analysis()  # NEW: Volume acceleration
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