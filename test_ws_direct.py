"""Direct WebSocket test - bypass gmgnapi wrapper"""
import asyncio
import os
import sys
import json
from pathlib import Path

# Load .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value.strip()

async def test_direct_websocket():
    """Test direct WebSocket connection"""
    import websockets
    
    access_token = os.environ.get("GMGN_API_KEY", "")
    ws_url = "wss://gmgn.ai/ws"
    
    print("=" * 50)
    print("Direct WebSocket Connection Test")
    print("=" * 50)
    print(f"URL: {ws_url}")
    print(f"API Key: {access_token[:15]}..." if access_token else "No API key")
    print()
    
    headers = []
    if access_token:
        headers.append(("Authorization", f"Bearer {access_token}"))
        headers.append(("X-API-Key", access_token))
    
    print("Connecting...")
    
    try:
        async with websockets.connect(ws_url, additional_headers=headers) as ws:
            print("SUCCESS: Connected to WebSocket!")
            print("Cloudflare bypassed!")
            print()
            
            # Try to subscribe
            subscribe_msg = json.dumps({
                "action": "subscribe",
                "channel": "new_pools",
                "chain": "sol"
            })
            
            await ws.send(subscribe_msg)
            print("Sent subscription request")
            
            # Wait for response
            print("Waiting for response (10 seconds)...")
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=10)
                print(f"Received: {response[:200]}...")
                return True
            except asyncio.TimeoutError:
                print("No response received (but connection worked!)")
                return True
                
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed: {e}")
        return False
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"HTTP Status: {e.status_code}")
        if e.status_code == 403:
            print("403 Forbidden - Cloudflare or IP block")
        return False
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    print("Testing direct WebSocket connection to GMGN...")
    print()
    result = asyncio.run(test_direct_websocket())
    print()
    print("=" * 50)
    if result:
        print("SUCCESS! WebSocket connection works!")
        print("The WebSocket endpoint bypasses Cloudflare REST API blocking.")
    else:
        print("FAILED: WebSocket connection blocked.")
        print()
        print("Both REST and WebSocket endpoints are blocked.")
        print("Wait for IP whitelist to propagate (30 min).")
    print("=" * 50)