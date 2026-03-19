# Solana Meme Coin Tracker - Free Version

## Data Sources (Free)
- **DexScreener API** - Price, volume, liquidity, social links
- **CoinGecko** - Market data, some social metrics  
- **Jupiter** - Price feeds
- **Helius** - Free tier for holder data (optional)

## How It Works
1. You forward contract messages from Telegram groups
2. I extract and store the contract address + initial data
3. HEARTBEAT checks run periodically to fetch updates
4. Alerts sent when thresholds are hit

## Tracked Metrics
- Price changes (1h, 24h)
- Volume spikes
- Holder growth
- Liquidity changes
- Age (to filter your criteria)
- Market cap

## Viral Signals
- Price pump >20% in 1h
- Volume spike >2x average
- Holder growth >10% in 24h
- Fresh wallet influx
- Social link activity (from scan data)

## Commands
- Forward any contract message → Auto-added to tracking
- "Narrative: [contract] = [story]" → Tag with context
- "Status" → Show current portfolio summary
- "Alerts" → Show recent threshold breaches