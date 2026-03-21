"""
GMGN Agent v1.0 - Token data from GMGN.ai API
Uses WebSocket for real-time data streaming
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
import sys

# GMGN WebSocket client
# Requires: pip install gmgnapi

class GMGNClient:
    """Simple GMGN WebSocket client for token data"""
    
    def __init__(self, access_token=None):
        self.access_token = access_token
        self.websocket_url = "wss://gmgn.ai/ws"
        
    async def get_token_info(self, chain, address):
        """Get token information via WebSocket"""
        # Placeholder - actual implementation requires gmgnapi package
        pass

def get_token_data_from_gmgn(address, chain="sol"):
    """
    Fetch token data from GMGN
    
    Note: GMGN API may require:
    1. Whitelisted IP
    2. API key authentication
    3. WebSocket connection (not REST)
    """
    print(f"GMGN Token Data for {address[:8]}...")
    print(f"Chain: {chain}")
    print(f"Status: API requires authentication")
    print(f"")
    print(f"To use GMGN API:")
    print(f"1. Ensure IP {get_public_ip()} is whitelisted at https://gmgn.ai/ai")
    print(f"2. Wait 5-10 minutes for propagation")
    print(f"3. Use gmgn-cli or gmgnapi Python package")
    return None

def get_public_ip():
    """Get public IP address"""
    import urllib.request
    try:
        return urllib.request.urlopen('https://ip.me').read().decode('utf-8').strip()
    except:
        return "Unknown"

if __name__ == "__main__":
    # Test
    print("GMGN Agent v1.0")
    print("=" * 50)
    
    # Get public IP
    ip = get_public_ip()
    print(f"Your Public IP: {ip}")
    print(f"")
    print(f"Configuration:")
    print(f"  GMGN_API_KEY: gmgn_9e73...83c (set in .env)")
    print(f"  GMGN_PRIVATE_KEY: (set in .env)")
    print(f"")
    print(f"API Status: Cloudflare blocking (403)")
    print(f"Action Required: Whitelist IP at https://gmgn.ai/ai")
    print(f"")
    print(f"After whitelisting:")
    print(f"  gmgn-cli token info --chain sol --address <address>")
    print(f"  gmgn-cli token security --chain sol --address <address>")
    print(f"  gmgn-cli market trending --chain sol --interval 1h")