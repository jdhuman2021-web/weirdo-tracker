# Squirmy Screener - Architecture Document

*Generated: 2026-03-21*

---

## System Overview

Squirmy Screener is a meme coin intelligence dashboard for tracking Solana tokens. It combines multiple data sources, AI scoring, and real-time updates to identify trading opportunities.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA COLLECTION LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ DexScreener  │  │   Helius     │  │   Jupiter    │  │   Supabase   │    │
│  │   (Prices)   │  │  (Holders)  │  │  (Real-time) │  │  (History)   │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
└─────────┼──────────────────┼──────────────────┼──────────────────┼───────────┘
          │                  │                  │                  │
          ▼                  ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AGENT PROCESSING LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Research   │──│   Helius     │──│    Whale     │──│   Jupiter    │    │
│  │   Agent      │  │   Agent      │  │   Agent      │  │   Agent      │    │
│  │   (v1.5)     │  │   (v1.0)     │  │   (v1.0)     │  │   (v1.0)     │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│         │                  │                  │                  │            │
│         ▼                  ▼                  ▼                  ▼            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │   Thinking   │──│   Backtest   │──│    Alert     │                      │
│  │   Agent      │  │   Agent      │  │   Agent      │                      │
│  │   (v2.4)     │  │   (v1.0)     │  │   (v1.0)     │                      │
│  └──────────────┘  └──────────────┘  └──────────────┘                      │
└─────────────────────────────────────────────────────────────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           STORAGE LAYER                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                          Supabase PostgreSQL                          │  │
│  │  Tables: tokens, price_snapshots, whale_activity, alerts,            │  │
│  │          pipeline_runs, score_history                                │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                          GitHub Repository                           │  │
│  │  Files: config/tokens.json, data/*.json (opportunities, latest)     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                                │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Dashboard (index.html)                              │  │
│  │  • Static hosting on Surge.sh                                         │  │
│  │  • Real-time price polling (DexScreener, 30s)                         │  │
│  │  • Full data refresh (GitHub Raw, 5min)                               │  │
│  │  • Supabase Realtime (instant score updates)                          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Sources

### 1. DexScreener API (Primary Price Data)

| Attribute | Value |
|-----------|-------|
| **Endpoint** | `https://api.dexscreener.com/latest/dex/tokens/{addresses}` |
| **Rate Limit** | ~300 requests/minute |
| **Cost** | Free |
| **Data** | Price USD, 24h change, volume, liquidity, market cap, social links |
| **Latency** | Real-time (~30 seconds) |
| **Usage** | Batch up to 30 addresses per request |

### 2. Helius API (Solana Blockchain Data)

| Attribute | Value |
|-----------|-------|
| **Endpoint** | `https://mainnet.helius-rpc.com/` |
| **Rate Limit** | 100,000 credits/month (free tier) |
| **Cost** | Free |
| **Data** | Holder count, fresh wallets, transaction history, token metadata, creator address |
| **Latency** | ~30 minutes (pipeline) |
| **Usage** | ~111 credits/day for 37 tokens |

### 3. Jupiter API (Real-time Prices)

| Attribute | Value |
|-----------|-------|
| **Endpoint** | `https://quote-api.jup.ag/v6/quote` |
| **Rate Limit** | ~10 requests/second |
| **Cost** | Free |
| **Data** | Real-time USD price, 24h change, block height |
| **Latency** | Real-time |
| **Usage** | Batch up to 50 tokens per request |

### 4. Supabase (Historical Data)

| Attribute | Value |
|-----------|-------|
| **Type** | PostgreSQL Database |
| **Free Tier** | 500MB storage, 2GB bandwidth/month |
| **Data** | Historical prices, scores, whale activity, alerts |
| **Features** | REST API, Realtime subscriptions |

---

## Agents (Pipeline Order)

### Pipeline Flow

```
Research → Helius → Whale → Jupiter → Thinking → Backtest → Alert → Commit
```

| Agent | Version | Input | Output | Purpose |
|-------|---------|-------|--------|---------|
| **Research Agent** | v1.5 | `config/tokens.json` | `data/latest.json` | Fetch token data from DexScreener |
| **Helius Agent** | v1.0 | `data/latest.json` | `data/helius_data.json` | Get holder counts, fresh wallets |
| **Whale Agent** | v1.0 | `data/latest.json` | `data/whale_activity.json` | Detect volume spikes, whale movements |
| **Jupiter Agent** | v1.0 | `config/tokens.json` | `data/jupiter_prices.json` | Get real-time Solana prices |
| **Thinking Agent** | v2.4 | All data | `data/opportunities.json` | AI scoring, BUY/SELL signals |
| **Backtest Agent** | v1.0 | `data/opportunities.json` | `data/backtest_results.json` | Track scoring accuracy |
| **Alert Agent** | v1.0 | `data/opportunities.json` | Telegram notification | Send alerts for high scores |

---

## Database Schema (Supabase)

### Tables

```sql
-- Tokens (37 tracked)
tokens (
  id UUID PRIMARY KEY,
  address TEXT UNIQUE,
  symbol TEXT,
  name TEXT,
  chain TEXT,
  status TEXT,  -- 'active', 'dead', 'removed'
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)

-- Price Snapshots (every 30 min)
price_snapshots (
  id UUID PRIMARY KEY,
  token_id UUID REFERENCES tokens,
  price_usd DECIMAL,
  price_change_1h DECIMAL,
  price_change_24h DECIMAL,
  volume_24h DECIMAL,
  liquidity_usd DECIMAL,
  market_cap DECIMAL,
  timestamp TIMESTAMP
)

-- Whale Activity
whale_activity (
  id UUID PRIMARY KEY,
  token_id UUID REFERENCES tokens,
  volume_spike_percent DECIMAL,
  detected_at TIMESTAMP,
  details JSONB
)

-- Alerts
alerts (
  id UUID PRIMARY KEY,
  token_id UUID REFERENCES tokens,
  alert_type TEXT,
  message TEXT,
  sent_at TIMESTAMP,
  status TEXT
)

-- Pipeline Runs
pipeline_runs (
  id UUID PRIMARY KEY,
  run_at TIMESTAMP,
  status TEXT,
  duration_seconds INTEGER,
  tokens_processed INTEGER,
  errors JSONB
)

-- Score History (for backtesting)
score_history (
  id UUID PRIMARY KEY,
  token_id UUID REFERENCES tokens,
  score INTEGER,
  recommendation TEXT,
  price_at_score DECIMAL,
  price_after_24h DECIMAL,
  price_after_7d DECIMAL,
  scored_at TIMESTAMP
)
```

---

## Scoring Algorithm (Thinking Agent v2.4)

### Score Components

| Factor | Weight | Max Points |
|--------|--------|------------|
| Price Change 24h | 15% | 15 |
| Volume 24h | 10% | 10 |
| Liquidity | 10% | 10 |
| Market Cap | 10% | 10 |
| Holder Count | 10% | 10 |
| Fresh Wallets | 10% | 10 |
| Whale Activity | 15% | 15 |
| Social Metrics | 5% | 5 |
| Historical Performance | 10% | 10 |
| Risk Factors | -20% | -20 (penalty) |

### Score Thresholds

| Score | Recommendation |
|-------|----------------|
| 85+ | STRONG_BUY |
| 70-84 | BUY |
| 55-69 | SPECULATIVE |
| 40-54 | WATCH |
| <40 | AVOID |

### Penalties Applied

| Condition | Penalty |
|-----------|---------|
| Price crashed >50% (24h) | -20 points |
| Liquidity < $10K | -10 points |
| No social links | -5 points |
| Holder count < 100 | -5 points |

---

## Dashboard (index.html)

### Hosting

| Attribute | Value |
|-----------|-------|
| **Platform** | Surge.sh |
| **URL** | https://squirmyscreener.surge.sh |
| **Cost** | Free (Student tier) |
| **Deployment** | `surge dashboard/ squirmyscreener.surge.sh` |

### Features

- **Real-time price polling**: DexScreener API every 30 seconds
- **Full data refresh**: GitHub Raw CDN every 5 minutes
- **Responsive design**: Mobile-friendly
- **Dark theme**: #0a0a0f background, #00ff88 accent
- **Score visualization**: Color-coded recommendations

### Data Flow

```
Browser → DexScreener API (30s) → Update prices
Browser → GitHub Raw (5min) → Update scores
Browser → Supabase Realtime → Instant score updates
```

---

## GitHub Actions Workflow

### Schedule

```yaml
on:
  schedule:
    - cron: '*/30 * * * *'  # Every 30 minutes
  workflow_dispatch:  # Manual trigger
```

### Environment Variables (Secrets)

| Secret | Used By |
|--------|---------|
| `HELIUS_API_KEY` | Helius Agent |
| `JUPITER_API_KEY` | Jupiter Agent |
| `SUPABASE_URL` | All agents |
| `SUPABASE_SERVICE_KEY` | All agents (write) |
| `TELEGRAM_BOT_TOKEN` | Alert Agent |
| `TELEGRAM_CHAT_ID` | Alert Agent |

### Pipeline Steps

```yaml
jobs:
  collect-data:
    steps:
      - Checkout
      - Setup Python 3.11
      - Install deps (requests, supabase)
      - Run Research Agent
      - Run Helius Agent
      - Run Whale Agent
      - Run Jupiter Agent
      - Run Thinking Agent
      - Run Backtest Agent
      - Run Alert Agent
      - Commit and Push Data
      - Pipeline Summary
```

---

## Cost Analysis

### Free Tier Usage

| Service | Free Tier | Our Usage | Status |
|---------|-----------|-----------|--------|
| DexScreener | 300 req/min | ~2 req/min | ✅ Within limits |
| Helius | 100K credits/mo | ~111 credits/day | ✅ Within limits |
| Jupiter | 10 req/sec | ~0.1 req/sec | ✅ Within limits |
| Supabase | 500MB / 2GB/mo | ~50MB / 200MB/mo | ✅ Within limits |
| Surge.sh | Unlimited | Static files | ✅ Free |
| GitHub Actions | 2000 min/mo | ~4320 min/mo | ⚠️ Exceeds free tier if run every 15min |

### Estimated Monthly Costs

- **Current (30-min schedule)**: **$0/month** (all free tier)
- **If reduced to 15-min**: Would exceed GitHub Actions free tier

---

## File Structure

```
.openclaw/workspace/
├── .github/
│   └── workflows/
│       └── tracker.yml          # GitHub Actions pipeline
├── agents/
│   ├── research_agent.py        # DexScreener fetch
│   ├── helius_agent.py         # Solana blockchain data
│   ├── whale_agent.py          # Volume spike detection
│   ├── jupiter_agent.py        # Real-time prices
│   ├── thinking_agent.py       # AI scoring
│   ├── backtest_agent.py       # Score accuracy tracking
│   └── alert_agent.py          # Telegram notifications
├── config/
│   └── tokens.json             # Token watchlist (37 tokens)
├── data/
│   ├── latest.json             # Current token data
│   ├── opportunities.json      # Scored opportunities
│   ├── helius_data.json        # Holder/wallet data
│   ├── jupiter_prices.json     # Real-time prices
│   ├── whale_activity.json     # Whale movements
│   └── backtest_history.json   # Historical accuracy
├── dashboard/
│   └── index.html              # Web dashboard
├── database/
│   ├── supabase_client.py      # Database client
│   └── migrations/
│       ├── 002_whale_intelligence.sql
│       ├── 003_score_history.sql
│       ├── 004_token_metadata.sql
│       └── 005_helius_fields.sql
├── .env                        # Local environment variables
└── requirements.txt            # Python dependencies
```

---

## Known Issues & Limitations

### Current Limitations

1. **30-minute latency**: Pipeline runs every 30 minutes to stay within GitHub Actions free tier
2. **Birdeye API broken**: Switched to Helius for holder data
3. **GMGN API blocked**: Cloudflare blocking requests (on hold)
4. **No historical charting**: Dashboard shows current state only

### Failed Integrations

| Service | Status | Reason |
|---------|--------|--------|
| Birdeye | ❌ Broken | API inconsistent, rate limited |
| GMGN | ❌ Blocked | Cloudflare 403 Forbidden |
| DEXScreener WebSocket | ❌ N/A | Not available for Solana |

---

## Future Roadmap

### Planned Improvements

1. **Supabase Realtime**: Instant score updates to dashboard
2. **Historical charts**: Track score performance over time
3. **Mobile app**: React Native dashboard
4. **More chains**: Ethereum, Base, Arbitrum support
5. **AI model improvement**: Train on historical backtest data

### Pending Migrations

- `005_helius_fields.sql` - Add holder_count, fresh_wallet_count fields

---

## API Keys (Secrets)

| Key | Service | Free Tier |
|-----|---------|-----------|
| `HELIUS_API_KEY` | Helius RPC | 100K credits/mo |
| `JUPITER_API_KEY` | Jupiter DEX | Unlimited |
| `SUPABASE_URL` | Supabase | 500MB |
| `SUPABASE_SERVICE_KEY` | Supabase Admin | - |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot | Unlimited |
| `OPENROUTER_API_KEY` | OpenRouter AI | 200 req/day |

---

## Summary

Squirmy Screener is a **free-tier meme coin intelligence system** that:

- Tracks **37 Solana tokens** from a configurable watchlist
- Runs **every 30 minutes** via GitHub Actions
- Uses **4 free APIs**: DexScreener, Helius, Jupiter, Supabase
- Produces **AI-scored recommendations**: STRONG_BUY to AVOID
- Deploys to **Surge.sh** for free static hosting
- Stores **historical data** in Supabase PostgreSQL
- Sends **Telegram alerts** for high-score tokens

**Total monthly cost: $0** (all within free tiers)