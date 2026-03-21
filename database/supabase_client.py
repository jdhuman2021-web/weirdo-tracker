"""
Supabase Database Client
Connects to Supabase PostgreSQL for cloud storage

Usage:
    from database.supabase_client import SupabaseClient
    
    client = SupabaseClient()
    client.upsert_token(...)
    client.insert_snapshot(...)
"""

import os
from datetime import datetime
from typing import Optional, Dict, List, Any

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("WARNING: supabase package not installed. Run: pip install supabase")


class SupabaseClient:
    """Client for Supabase database operations"""
    
    def __init__(self):
        """Initialize Supabase client with credentials from environment"""
        self.url = os.environ.get('SUPABASE_URL', '')
        self.key = os.environ.get('SUPABASE_KEY', '')
        self.client: Optional[Client] = None
        
        if not self.url or not self.key:
            print("WARNING: SUPABASE_URL or SUPABASE_KEY not set")
            return
        
        if not SUPABASE_AVAILABLE:
            print("WARNING: supabase not installed")
            return
        
        try:
            self.client = create_client(self.url, self.key)
            print(f"✅ Connected to Supabase: {self.url}")
        except Exception as e:
            print(f"ERROR connecting to Supabase: {e}")
            self.client = None
    
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self.client is not None
    
    # ============================================
    # TOKEN OPERATIONS
    # ============================================
    
    def upsert_token(self, symbol: str, name: str, address: str, 
                     chain: str = 'SOL', source: str = None, notes: str = None,
                     status: str = 'active') -> Optional[str]:
        """Insert or update a token"""
        if not self.is_connected():
            return None
        
        try:
            result = self.client.table('tokens').upsert({
                'symbol': symbol,
                'name': name,
                'address': address,
                'chain': chain,
                'source': source,
                'notes': notes,
                'status': status,
                'updated_at': datetime.utcnow().isoformat()
            }, on_conflict='address').execute()
            
            return result.data[0]['id'] if result.data else None
        except Exception as e:
            print(f"ERROR upserting token {symbol}: {e}")
            return None
    
    def get_all_tokens(self, status: str = 'active') -> List[Dict]:
        """Get all active tokens"""
        if not self.is_connected():
            return []
        
        try:
            result = self.client.table('tokens').select('*').eq('status', status).execute()
            return result.data
        except Exception as e:
            print(f"ERROR fetching tokens: {e}")
            return []
    
    def set_token_status(self, symbol: str, status: str) -> bool:
        """Mark a token as dead/active/paused"""
        if not self.is_connected():
            return False
        
        try:
            result = self.client.table('tokens').update({
                'status': status,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('symbol', symbol).execute()
            
            return len(result.data) > 0
        except Exception as e:
            print(f"ERROR updating token status: {e}")
            return False
    
    # ============================================
    # PRICE SNAPSHOT OPERATIONS
    # ============================================
    
    def insert_snapshot(self, token_address: str, price_usd: float, market_cap: float,
                        volume_24h: float, liquidity_usd: float,
                        price_change_1h: float, price_change_24h: float,
                        holder_count: int, age_hours: int, score: int, 
                        signal: str) -> Optional[str]:
        """Insert a price snapshot"""
        if not self.is_connected():
            return None
        
        try:
            result = self.client.table('price_snapshots').insert({
                'token_address': token_address,
                'price_usd': price_usd,
                'market_cap': market_cap,
                'volume_24h': volume_24h,
                'liquidity_usd': liquidity_usd,
                'price_change_1h': price_change_1h,
                'price_change_24h': price_change_24h,
                'holder_count': holder_count,
                'age_hours': age_hours,
                'score': score,
                'signal': signal
            }).execute()
            
            return result.data[0]['id'] if result.data else None
        except Exception as e:
            print(f"ERROR inserting snapshot: {e}")
            return None
    
    def get_latest_prices(self, limit: int = 50) -> List[Dict]:
        """Get latest prices using view"""
        if not self.is_connected():
            return []
        
        try:
            result = self.client.rpc('get_latest_prices', {}).execute()
            return result.data[:limit]
        except:
            # Fallback to direct query
            result = self.client.table('latest_prices').select('*').limit(limit).execute()
            return result.data
    
    def get_price_history(self, token_address: str, hours: int = 24) -> List[Dict]:
        """Get price history for a token"""
        if not self.is_connected():
            return []
        
        try:
            cutoff = datetime.utcnow().isoformat()
            result = self.client.table('price_snapshots').select('*') \
                .eq('token_address', token_address) \
                .gte('captured_at', f"NOW() - INTERVAL '{hours} hours'") \
                .order('captured_at', desc=True) \
                .execute()
            
            return result.data
        except Exception as e:
            print(f"ERROR fetching history: {e}")
            return []
    
    # ============================================
    # WHALE ACTIVITY OPERATIONS
    # ============================================
    
    def insert_whale_activity(self, token_address: str, whale_address: str,
                               whale_name: str, action: str, amount_usd: float,
                               tx_hash: str = None) -> Optional[str]:
        """Record whale activity"""
        if not self.is_connected():
            return None
        
        try:
            result = self.client.table('whale_activity').insert({
                'token_address': token_address,
                'whale_address': whale_address,
                'whale_name': whale_name,
                'action': action,
                'amount_usd': amount_usd,
                'tx_hash': tx_hash
            }).execute()
            
            return result.data[0]['id'] if result.data else None
        except Exception as e:
            print(f"ERROR inserting whale activity: {e}")
            return None
    
    def get_whale_activity(self, hours: int = 24) -> List[Dict]:
        """Get recent whale activity"""
        if not self.is_connected():
            return []
        
        try:
            result = self.client.table('whale_activity').select('*') \
                .gte('captured_at', f"NOW() - INTERVAL '{hours} hours'") \
                .order('captured_at', desc=True) \
                .execute()
            
            return result.data
        except Exception as e:
            print(f"ERROR fetching whale activity: {e}")
            return []
    
    # ============================================
    # ALERT OPERATIONS
    # ============================================
    
    def create_alert(self, token_address: str, alert_type: str, message: str,
                     score: int = None, threshold_type: str = None) -> Optional[str]:
        """Create an alert"""
        if not self.is_connected():
            return None
        
        try:
            result = self.client.table('alerts').insert({
                'token_address': token_address,
                'alert_type': alert_type,
                'message': message,
                'score': score,
                'threshold_type': threshold_type
            }).execute()
            
            return result.data[0]['id'] if result.data else None
        except Exception as e:
            print(f"ERROR creating alert: {e}")
            return None
    
    def get_unacknowledged_alerts(self) -> List[Dict]:
        """Get alerts that haven't been acknowledged"""
        if not self.is_connected():
            return []
        
        try:
            result = self.client.table('alerts').select('*') \
                .eq('acknowledged', False) \
                .order('created_at', desc=True) \
                .execute()
            
            return result.data
        except Exception as e:
            print(f"ERROR fetching alerts: {e}")
            return []
    
    # ============================================
    # PIPELINE RUN LOGGING
    # ============================================
    
    def log_pipeline_run(self, tokens_fetched: int, opportunities_found: int,
                          alerts_sent: int, status: str = 'success',
                          error_message: str = None, duration_seconds: float = None) -> Optional[str]:
        """Log a pipeline execution"""
        if not self.is_connected():
            return None
        
        try:
            result = self.client.table('pipeline_runs').insert({
                'tokens_fetched': tokens_fetched,
                'opportunities_found': opportunities_found,
                'alerts_sent': alerts_sent,
                'status': status,
                'error_message': error_message,
                'duration_seconds': duration_seconds
            }).execute()
            
            return result.data[0]['id'] if result.data else None
        except Exception as e:
            print(f"ERROR logging pipeline run: {e}")
            return None
    
    def get_recent_runs(self, limit: int = 10) -> List[Dict]:
        """Get recent pipeline runs"""
        if not self.is_connected():
            return []
        
        try:
            result = self.client.table('pipeline_runs').select('*') \
                .order('run_timestamp', desc=True) \
                .limit(limit) \
                .execute()
            
            return result.data
        except Exception as e:
            print(f"ERROR fetching pipeline runs: {e}")
            return []
    
    # ============================================
    # ANALYTICS
    # ============================================
    
    def get_token_summary(self) -> Dict:
        """Get summary statistics"""
        if not self.is_connected():
            return {}
        
        try:
            result = self.client.rpc('get_token_summary', {}).execute()
            return result.data[0] if result.data else {}
        except:
            # Manual query
            tokens = self.get_all_tokens()
            return {
                'total_tokens': len(tokens),
                'active_tokens': len([t for t in tokens if t.get('status') == 'active']),
                'dead_tokens': len([t for t in tokens if t.get('status') == 'dead'])
            }
    
    def get_top_performers(self, hours: int = 24, limit: int = 10) -> List[Dict]:
        """Get best performing tokens by score"""
        if not self.is_connected():
            return []
        
        try:
            # Query for top scores in last N hours
            result = self.client.table('price_snapshots').select('token_address, score') \
                .gte('captured_at', f"NOW() - INTERVAL '{hours} hours'") \
                .order('score', desc=True) \
                .limit(limit) \
                .execute()
            
            return result.data
        except Exception as e:
            print(f"ERROR fetching top performers: {e}")
            return []


    # ============================================
    # ASYNC METHODS FOR WEBSOCKET AGENT
    # ============================================
    
    async def insert_snapshot_async(self, token_address: str, price_usd: float, 
                                     market_cap: float, volume_24h: float, 
                                     liquidity_usd: float, price_change_1h: float,
                                     price_change_24h: float, holder_count: int,
                                     source: str = 'gmgn_websocket') -> Optional[str]:
        """Async insert snapshot for WebSocket agent"""
        return self.insert_snapshot(
            token_address=token_address,
            price_usd=price_usd,
            market_cap=market_cap,
            volume_24h=volume_24h,
            liquidity_usd=liquidity_usd,
            price_change_1h=price_change_1h,
            price_change_24h=price_change_24h,
            holder_count=holder_count,
            age_hours=0,  # Will be calculated
            score=0,  # Will be calculated by thinking agent
            signal='PENDING'
        )
    
    async def upsert_token_async(self, symbol: str, name: str, address: str,
                                  chain: str = 'SOL', source: str = 'gmgn_discovery') -> Optional[str]:
        """Async upsert token for WebSocket agent"""
        return self.upsert_token(
            symbol=symbol,
            name=name,
            address=address,
            chain=chain,
            source=source,
            status='active'
        )
    
    async def insert_whale_activity_async(self, token_address: str, whale_address: str,
                                           action: str, amount_usd: float,
                                           source: str = 'gmgn_websocket') -> Optional[str]:
        """Async insert whale activity for WebSocket agent"""
        return self.insert_whale_activity(
            token_address=token_address,
            whale_address=whale_address,
            whale_name='Unknown',
            action=action,
            amount_usd=amount_usd
        )


# Singleton instance
_client = None

def get_client() -> SupabaseClient:
    """Get or create Supabase client singleton"""
    global _client
    if _client is None:
        _client = SupabaseClient()
    return _client


if __name__ == "__main__":
    # Test connection
    client = get_client()
    if client.is_connected():
        print("✅ Supabase connection successful")
        
        # Test query
        tokens = client.get_all_tokens()
        print(f"📊 Tokens in database: {len(tokens)}")
    else:
        print("❌ Supabase connection failed")