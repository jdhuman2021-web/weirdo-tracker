"""Test GMGN WebSocket connection - Simple test"""
import asyncio
import os
import sys
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

async def test_connection():
    try:
        from gmgnapi import GmGnClient
    except ImportError:
        print("ERROR: gmgnapi not installed")
        return False
    
    access_token = os.environ.get("GMGN_API_KEY", "")
    
    print("=" * 50)
    print("GMGN WebSocket Connection Test")
    print("=" * 50)
    print(f"API Key: {access_token[:15]}..." if access_token else "No API key")
    print()
    
    print("Attempting to connect to wss://gmgn.ai/ws...")
    print()
    
    try:
        # Create client and connect
        client = GmGnClient(access_token=access_token if access_token else None)
        
        print("Client created successfully")
        print("Attempting to connect...")
        
        # Connect
        await client.connect()
        print("SUCCESS: Connected to GMGN WebSocket!")
        print("WebSocket bypassed Cloudflare!")
        
        # Subscribe to new pools
        await client.subscribe_new_pools(chain="sol")
        print("Subscribed to new_pools (sol)")
        
        # Listen for a bit
        print("Listening for 10 seconds...")
        await asyncio.sleep(10)
        
        # Disconnect
        await client.disconnect()
        print("Disconnected")
        return True
        
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        print()
        print("This likely means:")
        print("  1. IP not whitelisted at gmgn.ai/ai")
        print("  2. Invalid API key format")
        print("  3. WebSocket endpoint also blocked")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_connection())
    print()
    print("=" * 50)
    if result:
        print("WEBSOCKET CONNECTION SUCCESSFUL!")
    else:
        print("WEBSOCKET CONNECTION FAILED")
        print()
        print("The WebSocket endpoint may also be blocked.")
        print("Try again after IP whitelist propagates (30 min).")
    print("=" * 50)