# GMGN WebSocket Agent - Startup Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install websockets aiofiles python-dotenv
```

### 2. Configure API Keys
Already set in `.env`:
```
GMGN_API_KEY=gmgn_9e73819529f9b69ab51100d1cf13e83c
GMGN_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----...
```

### 3. Whitelist Your IP
1. Go to https://gmgn.ai/ai
2. Add your public IP
3. Wait 5-30 minutes for propagation

### 4. Run the Agent
```bash
# Windows
run_gmgn.bat

# Or directly
python agents\gmgn_websocket.py
```

## What It Does

### Real-time Data:
- Token price updates (every 30s)
- Volume and liquidity changes
- New pool discoveries
- Whale wallet trades

### Data Flow:
```
GMGN WebSocket → gmgn_websocket.py → Supabase → Dashboard
                                          ↓
                                    (future) Telegram alerts
```

### Tracked Tokens:
- All active tokens from `config/tokens.json`
- Auto-discovers new tokens
- Updates existing tokens every 30 seconds

## Architecture

```
┌─────────────────────┐
│   GMGN WebSocket    │
│   wss://gmgn.ai/ws  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  gmgn_websocket.py  │
│  - Subscribe tokens │
│  - Parse events     │
│  - Throttle 30s     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│     Supabase        │
│  - price_snapshots  │
│  - whale_activity   │
│  - Real-time pub    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│     Dashboard       │
│  - Real-time sub   │
│  - Instant updates  │
└─────────────────────┘
```

## Configuration

### Settings in `gmgn_websocket.py`:
```python
GMGN_WS_URL = "wss://gmgn.ai/ws"
UPDATE_INTERVAL = 30  # seconds
TRACK_ALL_TOKENS = True
AUTO_DISCOVER = True
```

### Environment Variables:
```
GMGN_API_KEY        # Your GMGN API key
GMGN_PRIVATE_KEY    # Ed25519 private key for signing
```

## Logs

Console output shows:
```
🚀 GMGN WebSocket Agent v1.0
✅ Connected to GMGN WebSocket
📡 Subscribed to token_updates for 37 tokens
📡 Subscribed to new_pools on sol
📡 Subscribed to wallet_trades
🎧 Listening for updates...

💰 DEVI: $0.0000624
💰 PUNCH: $0.01466
🐋 Whale: buy $50,000 on DEVI...
🆕 New token: CeoReCwA...
```

## Troubleshooting

### Connection Failed
1. Check IP is whitelisted at gmgn.ai/ai
2. Wait 30 minutes for propagation
3. Verify API key is correct

### No Data Coming Through
1. Check WebSocket connection is active
2. Verify tokens are loaded from config
3. Check Supabase connection

### Rate Limiting
- GMGN may throttle if too many subscriptions
- Batch size is limited to 50 tokens per subscription
- Update interval is 30 seconds minimum

## Next Steps

1. Enable Supabase real-time broadcasts
2. Update dashboard to subscribe to changes
3. Add Telegram alerts for whales
4. Monitor and optimize performance