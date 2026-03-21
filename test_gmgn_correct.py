"""Test GMGN API with correct header format"""
import asyncio
import os
import sys
import json
from pathlib import Path
import urllib.request
import urllib.error

# Load .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value.strip()

def test_rest_api():
    """Test REST API with correct header"""
    api_key = os.environ.get("GMGN_API_KEY", "")
    
    print("=" * 50)
    print("GMGN REST API Test (Correct Header)")
    print("=" * 50)
    print(f"API Key: {api_key[:15]}...")
    print()
    
    # Test with correct header
    url = "https://gmgn.ai/defi/router/v1/sol/tx/get_swap_route?token_in_address=So11111111111111111111111111111111111111112&token_out_address=CeoReCwAmt8iqjQoKQGEMqKERDWGxxDUED9zVYg3pump&in_amount=1000000&from_address=2kpJ5QRh16aRQoLZ5LnucHFDAZtEFz6omqWWMzDSNrx&slippage=0.5"
    
    print(f"Testing: {url[:60]}...")
    print()
    
    try:
        req = urllib.request.Request(url)
        # Correct header format
        req.add_header('x-route-key', api_key)
        req.add_header('User-Agent', 'Mozilla/5.0')
        
        response = urllib.request.urlopen(req, timeout=10)
        data = response.read().decode('utf-8')
        
        print("SUCCESS! Response:")
        print(data[:500])
        return True
        
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print(f"Headers: {e.headers}")
        print(f"Body: {e.read().decode('utf-8')[:500]}")
        return False
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return False

async def test_websocket_correct():
    """Test WebSocket with correct authentication"""
    import websockets
    
    api_key = os.environ.get("GMGN_API_KEY", "")
    ws_url = "wss://gmgn.ai/ws"
    
    print()
    print("=" * 50)
    print("GMGN WebSocket Test (Correct Header)")
    print("=" * 50)
    print(f"URL: {ws_url}")
    print(f"API Key: {api_key[:15]}...")
    print()
    
    headers = [
        ("x-route-key", api_key),
        ("User-Agent", "Mozilla/5.0")
    ]
    
    print("Connecting with x-route-key header...")
    
    try:
        async with websockets.connect(ws_url, additional_headers=headers) as ws:
            print("SUCCESS! WebSocket connected!")
            print("Cloudflare bypassed!")
            
            subscribe_msg = json.dumps({
                "action": "subscribe",
                "channel": "new_pools",
                "chain": "sol"
            })
            
            await ws.send(subscribe_msg)
            print("Sent subscription request")
            
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=10)
                print(f"Received: {response[:200]}...")
                return True
            except asyncio.TimeoutError:
                print("No response (but connection worked!)")
                return True
                
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    print("Testing GMGN API with correct authentication header...")
    print()
    
    # Test REST API
    rest_result = test_rest_api()
    
    # Test WebSocket
    ws_result = asyncio.run(test_websocket_correct())
    
    print()
    print("=" * 50)
    if rest_result or ws_result:
        print("SUCCESS! At least one endpoint works!")
    else:
        print("FAILED: Both endpoints blocked.")
        print()
        print("NEXT STEPS:")
        print("1. Apply for API access: https://forms.gle/CWABDLRe8twvygvy5")
        print("2. Wait for approval (24 hours)")
        print("3. Use correct header: x-route-key")
    print("=" * 50)