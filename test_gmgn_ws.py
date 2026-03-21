"""Test GMGN WebSocket connection"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def load_env():
    """Load .env file manually"""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value

load_env()

async def test_websocket():
    try:
        import websockets
    except ImportError:
        print("❌ websockets module not installed")
        print("Run: pip install websockets")
        return False
    
    api_key = os.environ.get("GMGN_API_KEY", "")
    ws_url = "wss://gmgn.ai/ws"
    
    print(f"🔌 Testing WebSocket connection to {ws_url}")
    print(f"🔑 Using API key: {api_key[:15]}..." if api_key else "❌ No API key found")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-API-Key": api_key,
    }
    
    try:
        print("\n🔄 Connecting...")
        async with websockets.connect(ws_url, extra_headers=headers, ping_interval=30) as ws:
            print("✅ Connected! WebSocket connection established")
            
            # Try to subscribe
            import json
            subscribe_msg = {
                "action": "subscribe",
                "channel": "token_updates",
                "tokens": ["CeoReCwAmt8iqjQoKQGEMqKERDWGxxDUED9zVYg3pump"]
            }
            
            await ws.send(json.dumps(subscribe_msg))
            print("📡 Sent subscription request")
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=10)
                print(f"📥 Received: {response[:200]}...")
                return True
            except asyncio.TimeoutError:
                print("⏱️ No response within 10 seconds (but connection worked!)")
                return True
                
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ Connection closed: {e}")
        return False
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Invalid status code: {e}")
        print("   This usually means authentication failed or Cloudflare blocked")
        return False
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_websocket())
    print(f"\n{'✅ Success!' if result else '❌ Failed'}")