# Research Agent

## Installation

```bash
# Install dependencies
pip install requests

# Run the agent
python research_agent.py
```

## Output Format

The agent produces JSON files in `data/` directory:

```json
{
  "metadata": {
    "timestamp": "2025-03-20T09:30:00",
    "tokens_count": 20,
    "source": "research_agent_v1.0"
  },
  "data": [
    {
      "symbol": "PUNCH",
      "name": "パンチ",
      "address": "NV2RYH...",
      "chain": "SOL",
      "price_usd": 0.01483,
      "price_change_1h": 0.94,
      "price_change_24h": 21.18,
      "volume_24h": 1429185,
      "liquidity_usd": 743000,
      "market_cap": 14890000,
      "txns_24h": {"buys": 150, "sells": 89},
      "timestamp": "2025-03-20T09:30:00",
      "source": "dexscreener"
    }
  ]
}
```

## Data Sources

- **DexScreener API**: Prices, volume, liquidity
- **Rate limit**: 10 requests/minute
- **Update frequency**: Every 15 minutes recommended

## Next Steps

1. Run this agent to collect data
2. Pass output to Thinking Agent for analysis
3. Thinking Agent produces scored opportunities
4. Alert Agent sends notifications
