---
name: solana-meme-tracker
description: Track Solana meme coins from forwarded Telegram/Discord scan messages. Extract contract addresses, monitor price/volume/holder metrics, and alert on viral signals. Use when user forwards contract scan messages, asks to track meme coins, or wants alerts on Solana token movements. Supports Rick Burp Bot format and manual contract input.
---

# Solana Meme Coin Tracker

Track Solana meme coins from forwarded scan messages and monitor for viral signals.

## Quick Start

1. **Forward scan messages** from Telegram groups (Rick Burp Bot format supported)
2. **Or paste contract addresses** directly
3. **View portfolio** anytime with "status" command
4. **Get alerts** on price pumps, volume spikes, holder growth

## Supported Data Sources

- Rick Burp Bot (Telegram) - Full auto-extraction
- Manual contract addresses - Requires follow-up for data
- DexScreener API (free) - Price, volume, liquidity
- CoinGecko API (free tier) - Market data

## Commands

| Command | Action |
|---------|--------|
| Forward scan message | Auto-extract and track contract |
| Paste contract address | Add to tracker (fetch data later) |
| "status" | Show current portfolio summary |
| "alerts" | Show recent threshold breaches |
| "narrative: [symbol] = [story]" | Tag token with narrative |

## Tracked Metrics

- Price (USD)
- Market Cap
- FDV (Fully Diluted Valuation)
- Liquidity
- 24h Volume
- Holder count
- Fresh wallet % (1D, 7D)
- Age

## Alert Thresholds

Auto-alert when:
- Price change >20% (1h) or >50% (24h)
- Volume spikes >2x average
- Holder growth >10% (24h)
- Liquidity drains >30%

## Data Storage

Contracts stored in: `~/.openclaw/workspace/solana_tracker.json`

## Scripts

- `scripts/extract_contract.py` - Parse scan messages for contract data
- `scripts/fetch_updates.py` - Query APIs for latest metrics
- `scripts/check_alerts.py` - Compare current vs thresholds

## References

- `references/api_endpoints.md` - Free API documentation
- `references/scan_formats.md` - Supported message formats

## Filters

Default filters (adjustable):
- Market cap: 0 - 50K (for microcap hunting)
- Age: >2 days (avoid immediate rugs)
- Liquidity: >10K (ensure tradable)

## Example Workflow

1. User forwards: `[💊] [TokenName] [MCAP/X%] $SYMBOL ...`
2. Skill extracts: contract address, symbol, all metrics
3. Saves to tracker with timestamp
4. HEARTBEAT checks for updates every 30 min
5. Alerts sent when thresholds breached