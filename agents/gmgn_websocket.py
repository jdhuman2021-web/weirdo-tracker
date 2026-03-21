"""
GMGN WebSocket Agent v1.0
Real-time token data from GMGN.ai

Subscribes to:
- token_updates: Price, volume, liquidity updates
- new_pools: Discover new tokens
- wallet_trades: Track whale activity

Usage:
    python agents/gmgn_websocket.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Callable

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuration
GMGN_WS_URL = "wss://gmgn.ai/ws"
UPDATE_INTERVAL = 30  # seconds
TRACK_ALL_TOKENS = True
AUTO_DISCOVER = True

class GMGNWebSocketClient:
    """WebSocket client for GMGN.ai real-time data"""
    
    def __init__(self, api_key: str, private_key: str = None):
        self.api_key = api_key
        self.private_key = private_key
        self.ws_url = GMGN_WS_URL
        self.websocket = None
        self.running = False
        self.subscriptions = []
        
        # Token tracking
        self.tracked_tokens: Dict[str, dict] = {}
        self.last_update: Dict[str, datetime] = {}
        
        # Callbacks
        self.on_token_update: Optional[Callable] = None
        self.on_new_pool: Optional[Callable] = None
        self.on_wallet_trade: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
    async def connect(self):
        """Connect to GMGN WebSocket"""
        import websockets
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-API-Key": self.api_key
        }
        
        try:
            self.websocket = await websockets.connect(
                self.ws_url,
                extra_headers=headers,
                ping_interval=30,
                ping_timeout=10
            )
            self.running = True
            print(f"✅ Connected to GMGN WebSocket")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            if self.on_error:
                await self.on_error(f"Connection failed: {e}")
            return False
    
    async def subscribe_token_updates(self, tokens: List[str]):
        """Subscribe to price updates for specific tokens"""
        subscription = {
            "action": "subscribe",
            "channel": "token_updates",
            "tokens": tokens
        }
        await self.websocket.send(json.dumps(subscription))
        self.subscriptions.append("token_updates")
        print(f"📡 Subscribed to token_updates for {len(tokens)} tokens")
    
    async def subscribe_new_pools(self, chain: str = "sol"):
        """Subscribe to new pool discoveries"""
        subscription = {
            "action": "subscribe",
            "channel": "new_pools",
            "chain": chain
        }
        await self.websocket.send(json.dumps(subscription))
        self.subscriptions.append("new_pools")
        print(f"📡 Subscribed to new_pools on {chain}")
    
    async def subscribe_wallet_trades(self, wallets: List[str] = None):
        """Subscribe to wallet trade events"""
        subscription = {
            "action": "subscribe",
            "channel": "wallet_trades"
        }
        if wallets:
            subscription["wallets"] = wallets
        await self.websocket.send(json.dumps(subscription))
        self.subscriptions.append("wallet_trades")
        print(f"📡 Subscribed to wallet_trades")
    
    async def listen(self):
        """Listen for incoming messages"""
        while self.running:
            try:
                message = await asyncio.wait_for(
                    self.websocket.recv(),
                    timeout=60
                )
                data = json.loads(message)
                await self._handle_message(data)
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await self.websocket.ping()
            except websockets.exceptions.ConnectionClosed:
                print("⚠️ Connection closed, reconnecting...")
                await self._reconnect()
            except Exception as e:
                print(f"❌ Error in listen loop: {e}")
                if self.on_error:
                    await self.on_error(f"Listen error: {e}")
    
    async def _handle_message(self, data: dict):
        """Handle incoming WebSocket message"""
        channel = data.get("channel")
        event = data.get("event")
        payload = data.get("data", {})
        
        if channel == "token_updates":
            await self._handle_token_update(payload)
        elif channel == "new_pools":
            await self._handle_new_pool(payload)
        elif channel == "wallet_trades":
            await self._handle_wallet_trade(payload)
    
    async def _handle_token_update(self, data: dict):
        """Handle token price update"""
        address = data.get("address")
        
        # Throttle updates (30s minimum between updates per token)
        now = datetime.utcnow()
        if address in self.last_update:
            elapsed = (now - self.last_update[address]).total_seconds()
            if elapsed < UPDATE_INTERVAL:
                return
        
        self.last_update[address] = now
        
        # Update tracked token
        if address in self.tracked_tokens:
            self.tracked_tokens[address].update({
                "price_usd": data.get("price_usd"),
                "price_change_1h": data.get("change_1h"),
                "price_change_24h": data.get("change_24h"),
                "volume_24h": data.get("volume_24h"),
                "liquidity_usd": data.get("liquidity"),
                "market_cap": data.get("market_cap"),
                "timestamp": now.isoformat()
            })
        
        # Call callback
        if self.on_token_update:
            await self.on_token_update(address, data)
    
    async def _handle_new_pool(self, data: dict):
        """Handle new pool discovery"""
        if not AUTO_DISCOVER:
            return
        
        address = data.get("address")
        chain = data.get("chain", "sol")
        
        print(f"🆕 New pool discovered: {address[:8]}... on {chain}")
        
        # Auto-add to tracked tokens
        self.tracked_tokens[address] = {
            "address": address,
            "chain": chain,
            "symbol": data.get("symbol", "UNKNOWN"),
            "name": data.get("name", "Unknown"),
            "discovered_at": datetime.utcnow().isoformat(),
            "auto_discovered": True
        }
        
        if self.on_new_pool:
            await self.on_new_pool(address, data)
    
    async def _handle_wallet_trade(self, data: dict):
        """Handle whale wallet trade"""
        wallet = data.get("wallet")
        token = data.get("token")
        amount_usd = data.get("amount_usd", 0)
        action = data.get("action", "unknown")
        
        # Log significant trades
        if amount_usd > 10000:  # $10K+
            print(f"🐋 Large trade: {action} ${amount_usd:,.0f} on {token[:8]}...")
        
        if self.on_wallet_trade:
            await self.on_wallet_trade(wallet, token, amount_usd, action)
    
    async def _reconnect(self):
        """Reconnect to WebSocket"""
        max_retries = 5
        retry_delay = 5
        
        for attempt in range(max_retries):
            print(f"🔄 Reconnecting (attempt {attempt + 1}/{max_retries})...")
            if await self.connect():
                # Re-subscribe to channels
                if "token_updates" in self.subscriptions:
                    tokens = list(self.tracked_tokens.keys())
                    await self.subscribe_token_updates(tokens)
                if "new_pools" in self.subscriptions:
                    await self.subscribe_new_pools()
                if "wallet_trades" in self.subscriptions:
                    await self.subscribe_wallet_trades()
                return True
            
            await asyncio.sleep(retry_delay * (attempt + 1))
        
        print(f"❌ Failed to reconnect after {max_retries} attempts")
        return False
    
    async def close(self):
        """Close WebSocket connection"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            print("🔌 Disconnected from GMGN")


class GMGNDataProcessor:
    """Process and score real-time data from GMGN"""
    
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self.token_cache: Dict[str, dict] = {}
    
    async def process_token_update(self, address: str, data: dict):
        """Process token update and write to Supabase"""
        now = datetime.utcnow()
        
        # Cache update
        self.token_cache[address] = {
            **data,
            "last_update": now.isoformat()
        }
        
        # Write to Supabase
        if self.supabase and self.supabase.is_connected():
            try:
                await self.supabase.insert_snapshot_async(
                    token_address=address,
                    price_usd=data.get("price_usd", 0),
                    market_cap=data.get("market_cap", 0),
                    volume_24h=data.get("volume_24h", 0),
                    liquidity_usd=data.get("liquidity", 0),
                    price_change_1h=data.get("change_1h", 0),
                    price_change_24h=data.get("change_24h", 0),
                    holder_count=data.get("holder_count", 0),
                    source="gmgn_websocket"
                )
            except Exception as e:
                print(f"❌ Failed to write to Supabase: {e}")
    
    async def process_new_token(self, address: str, data: dict):
        """Process new token discovery"""
        # Add to local tracking
        print(f"➕ Added new token: {address[:8]}...")
        
        # Write to Supabase
        if self.supabase and self.supabase.is_connected():
            try:
                await self.supabase.upsert_token_async(
                    symbol=data.get("symbol", "UNKNOWN"),
                    name=data.get("name", "Unknown"),
                    address=address,
                    chain=data.get("chain", "SOL"),
                    source="gmgn_discovery"
                )
            except Exception as e:
                print(f"❌ Failed to add token: {e}")
    
    async def process_whale_trade(self, wallet: str, token: str, amount: float, action: str):
        """Process whale trade"""
        # Write to Supabase
        if self.supabase and self.supabase.is_connected():
            try:
                await self.supabase.insert_whale_activity_async(
                    token_address=token,
                    whale_address=wallet,
                    action=action,
                    amount_usd=amount,
                    source="gmgn_websocket"
                )
            except Exception as e:
                print(f"❌ Failed to log whale trade: {e}")


def load_tracked_tokens() -> Dict[str, dict]:
    """Load tracked tokens from config"""
    config_path = Path("config/tokens.json")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            tokens = {}
            for token in config.get("tokens", []):
                if token.get("status", "active") != "dead":
                    tokens[token["address"]] = {
                        "symbol": token.get("symbol"),
                        "name": token.get("name"),
                        "chain": token.get("chain", "SOL"),
                        "status": token.get("status", "active")
                    }
            return tokens
    return {}


async def main():
    """Main WebSocket client loop"""
    from dotenv import load_dotenv
    
    # Load environment
    load_dotenv()
    
    api_key = os.getenv("GMGN_API_KEY")
    private_key = os.getenv("GMGN_PRIVATE_KEY")
    
    if not api_key:
        print("❌ GMGN_API_KEY not found in .env")
        return
    
    print("🚀 GMGN WebSocket Agent v1.0")
    print("=" * 50)
    print(f"📡 Connecting to {GMGN_WS_URL}")
    print(f"⏱️  Update interval: {UPDATE_INTERVAL}s")
    print(f"🔍 Auto-discover: {AUTO_DISCOVER}")
    print()
    
    # Load tracked tokens
    tracked_tokens = load_tracked_tokens()
    print(f"📋 Tracking {len(tracked_tokens)} tokens")
    
    # Initialize client
    client = GMGNWebSocketClient(api_key, private_key)
    client.tracked_tokens = tracked_tokens
    
    # Initialize processor
    processor = GMGNDataProcessor()
    
    # Set callbacks
    async def on_token_update(address, data):
        print(f"💰 {tracked_tokens.get(address, {}).get('symbol', address[:8])}: ${data.get('price_usd', 0):.6f}")
        await processor.process_token_update(address, data)
    
    async def on_new_pool(address, data):
        print(f"🆕 New token: {address[:8]}...")
        await processor.process_new_token(address, data)
    
    async def on_whale_trade(wallet, token, amount, action):
        if amount > 10000:
            print(f"🐋 Whale: {action} ${amount:,.0f} on {token[:8]}...")
        await processor.process_whale_trade(wallet, token, amount, action)
    
    async def on_error(error):
        print(f"❌ Error: {error}")
    
    client.on_token_update = on_token_update
    client.on_new_pool = on_new_pool
    client.on_wallet_trade = on_whale_trade
    client.on_error = on_error
    
    # Connect
    if not await client.connect():
        return
    
    # Subscribe to channels
    if TRACK_ALL_TOKENS:
        token_addresses = list(tracked_tokens.keys())
        # Subscribe in batches of 50 (GMGN limit)
        batch_size = 50
        for i in range(0, len(token_addresses), batch_size):
            batch = token_addresses[i:i + batch_size]
            await client.subscribe_token_updates(batch)
            await asyncio.sleep(1)  # Rate limit
    
    if AUTO_DISCOVER:
        await client.subscribe_new_pools()
    
    await client.subscribe_wallet_trades()
    
    # Listen for messages
    print("\n🎧 Listening for updates...")
    print("Press Ctrl+C to stop\n")
    
    try:
        await client.listen()
    except KeyboardInterrupt:
        print("\n⏹️ Stopping...")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())