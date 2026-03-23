# Squirmy Screener - Architecture v2.0

*Last Updated: 2026-03-23*

## Overview

Squirmy Screener is a meme coin intelligence platform that combines multiple data sources to identify trading opportunities on Solana. This document describes the current architecture including the new SolanaTracker integration.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA SOURCES                                       │
├──────────────┬──────────────┬──────────────┬──────────────┬──────────────┤
│ DexScreener  │ SolanaTracker│   Helius     │   Supabase   │   GitHub     │
│   (Prices)   │  (Security)  │  (Metadata)  │  (History)   │   (Config)   │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┘
       │              │              │              │              │
       └──────────────┴──────────────┴──────────────┴──────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      COLLECT & SCORE PIPELINE v1.0                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Research   │──│   Holders    │──│    Whale     │──│   Thinking   │   │
│  │   (v1.5)     │  │   (v2.0)     │  │   (v1.0)     │  │   (v2.5)     │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────┬───────┘   │
│         │                                                      │            │
│         │              ┌───────────────────────────────────────┘            │
│         │              │                                                    │
│         │              ▼                                                    │
│         │       ┌──────────────┐                                            │
│         │       │   MERGE      │                                            │
│         │       │ SolanaTracker│                                            │
│         │       │   Data       │                                            │
│         │       └──────┬───────┘                                            │
│         │              │                                                    │
│         └──────────────┼────────────────────────────────────────────────────┘
│                        │
│                        ▼
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  │   Backtest   │──│    Alert     │──│    Save      │
│  │   (v1.0)     │  │   (v1.0)     │  │   (v1.0)     │
│  └──────────────┘  └──────────────┘  └──────────────┘
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STORAGE & OUTPUT                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │opportunities.│  │   latest.    │  │   Supabase   │  │   Telegram   │  │
│  │    json      │  │    json      │  │     DB       │  │   Alerts     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DASHBOARD                                          │
│                    https://squirmyscreener.surge.sh                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Sources

### 1. DexScreener API (Primary)

| Attribute | Value |
|-----------|-------|
| **Endpoint** | `https://api.dexscreener.com/latest/dex/tokens/{addresses}` |
| **Rate Limit** | ~300 requests/minute |
| **Cost** | Free |
| **Data** | Price USD, 24h change, volume, liquidity, market cap, social links |
| **Latency** | Real-time (~30 seconds) |
| **Update Frequency** | Every 30 minutes (pipeline) + Real-time polling (dashboard) |

### 2. SolanaTracker API (Security & Analytics)

| Attribute | Value |
|-----------|-------|
| **Endpoint** | `https://data.solanatracker.io/tokens/{address}` |
| **Rate Limit** | 1000 credits/month (free tier) |
| **Cost** | Free (1000 credits/month) |
| **Data** | Security metrics, holder counts, transaction analysis, social links |
| **Latency** | ~2 seconds per token |
| **Update Strategy** | Optimized (see below) |

### 3. Helius API (Metadata)

| Attribute | Value |
|-----------|-------|
| **Endpoint** | `https://api.helius.xyz/v0/token-metadata` |
| **Rate Limit** | 100K credits/month |
| **Cost** | Free |
| **Data** | Token metadata, creation info |
| **Status** | Backup source |

### 4. Supabase (Historical Data)

| Attribute | Value |
|-----------|-------|
| **Type** | PostgreSQL Database |
| **Free Tier** | 500MB storage, 2GB bandwidth/month |
| **Data** | Historical prices, scores, alerts, pipeline runs |
| **Features** | REST API, Realtime subscriptions |

---

## Optimized SolanaTracker Strategy

### Credit Usage Optimization

| Data Type | Collection Strategy | Credits/Month |
|-----------|---------------------|---------------|
| **Static Data** (LP burn, socials, security) | Fetch once, cache forever | ~26 (one-time) |
| **Dynamic Data** (holders, transactions) | Refresh every 2 days | ~104 (26 tokens × 4 refreshes) |
| **Total** | | **~130 credits/month** |
| **Budget** | 1000 credits/month | |
| **Savings** | | **87% reduction** |

### Static Data (Cache Forever)

```python
# Fetched once per token, never changes
{
    "security_score": 95,        # Calculated from LP burn + authorities
    "lp_burn": 99,               # LP tokens burned (immutable)
    "freeze_authority": null,    # Can freeze wallets?
    "mint_authority": null,      # Can mint more tokens?
    "twitter": "url",            # Social links
    "telegram": "url",
    "website": "url",
    "creation_time": 1770281242, # Token birth timestamp
    "deployer": "address"        # Creator wallet
}
```

### Dynamic Data (Refresh Every 2 Days)

```python
# Updated regularly to track changes
{
    "holders": 26772,              # Number of token holders
    "token_supply": 999849956,     # Total token supply
    "buys": 397323,                # Buy transactions
    "sells": 363002,               # Sell transactions
    "total_txns": 760325,          # Total transactions
    "volume_24h": 1529319,         # 24h volume in USD
    "buy_sell_ratio": 1.09         # Buys/sells ratio
}
```

### Caching Mechanism

```
Token Cache (solanatracker_cache.json)
├── Token Address (key)
│   ├── Static Data (fetched once)
│   ├── Dynamic Data (updated every 2 days)
│   └── Timestamps (for cache validation)
```

---

## Pipeline Flow

### Step 1: Research (DexScreener)

```python
# Fetch all tokens from DexScreener
# Returns: price, volume, liquidity, market cap, social links
# Time: ~4-5 minutes (26 tokens × 6s delay)
```

### Step 2: Holders (DexScreener + Fallback)

```python
# Try DEXScreener holders field first
# Fallback to SolanaTracker data (cached)
# Time: ~1 minute
```

### Step 3: Whale Detection

```python
# Calculate volume spikes
# Detect unusual trading patterns
# Time: ~30 seconds
```

### Step 4: Thinking (Scoring)

```python
# Calculate opportunity scores
# Consider price, volume, liquidity, age
# Time: ~1 minute
```

### Step 5: Merge SolanaTracker Data

```python
# Load cached SolanaTracker data
# Merge into opportunities:
#   - Security score
#   - Holder counts
#   - Buy/sell ratio
#   - Token age
#   - Social links
# Time: ~10 seconds
```

### Step 6: Backtest

```python
# Save snapshot for accuracy tracking
# Compare predictions vs outcomes
# Time: ~30 seconds
```

### Step 7: Alert

```python
# Check for high scores
# Send Telegram notifications
# Time: ~10 seconds
```

### Step 8: Save & Commit

```python
# Write opportunities.json (with merged data)
# Write latest.json
# Write Supabase
# Git commit & push
# Time: ~1 minute
```

---

## Scoring Algorithm v2.5

### Base Components (from DexScreener)

| Factor | Weight | Max Points |
|--------|--------|------------|
| Price Change 24h | 15% | 15 |
| Volume 24h | 10% | 10 |
| Liquidity | 10% | 10 |
| Market Cap | 10% | 10 |
| Age Timing | 5% | 5 |
| Whale Activity | 15% | 15 |
| **Total Base** | **65%** | **65** |

### SolanaTracker Enhancements (NEW)

| Factor | Weight | Max Points | Source |
|--------|--------|------------|--------|
| Security Score | 15% | 15 | LP burn + authorities |
| Holder Growth | 10% | 10 | SolanaTracker holders |
| Buy/Sell Pressure | 10% | 10 | Transaction ratio |
| **Total Enhanced** | **35%** | **35** |

### Security Scoring

```python
# LP Burn (40 points max)
100% burned:  40 points
95-99%:       35 points
90-94%:       30 points
80-89%:       20 points
50-79%:       10 points
<50%:          0 points

# Freeze Authority (30 points)
None:          30 points
Present:        0 points

# Mint Authority (30 points)
None:          30 points
Present:        0 points

# Total: 100 points max
```

---

## Data Flow

```
┌─────────────────┐
│  GitHub Actions │  (Every 30 minutes)
│   Scheduler     │
└────────┬────────┘
         │
         ▼
┌────────────────────────────────────────────────────────┐
│ 1. SolanaTracker Agent v2.0                            │
│    ├─ Check cache for each token                       │
│    ├─ New tokens: Fetch static + dynamic data           │
│    ├─ Existing: Refresh dynamic data (every 2 days)   │
│    └─ Save to solanatracker_cache.json                │
└────────┬───────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────┐
│ 2. Collect & Score Pipeline                          │
│    ├─ Research: DexScreener prices (5 min)            │
│    ├─ Holders: Cached SolanaTracker data              │
│    ├─ Whale: Volume spike detection                   │
│    ├─ Thinking: Calculate scores                      │
│    ├─ MERGE: Add SolanaTracker security/holders      │
│    ├─ Backtest: Save snapshot                       │
│    ├─ Alert: Telegram notifications                  │
│    └─ Save: opportunities.json (with merged data)    │
└────────┬───────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────┐
│ 3. Git Commit & Push                                   │
│    ├─ opportunities.json → GitHub                       │
│    ├─ latest.json → GitHub                            │
│    └─ Trigger: Surge.sh redeploy                      │
└────────┬───────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────┐
│ 4. Dashboard Updates                                   │
│    ├─ GitHub Raw CDN (5 min cache)                    │
│    ├─ Dashboard loads opportunities.json              │
│    ├─ Shows Security Score, Holders, Buy/Sell        │
│    └─ Real-time price polling (DexScreener)          │
└────────────────────────────────────────────────────────┘
```

---

## File Structure

```
.openclaw/workspace/
├── .github/
│   └── workflows/
│       └── tracker.yml              # GitHub Actions pipeline
├── agents/
│   ├── collect_and_score.py       # Main pipeline (includes merge)
│   ├── solanatracker_agent_v2.py   # Optimized SolanaTracker agent
│   ├── merge_solanatracker.py      # Standalone merge (deprecated)
│   └── ...
├── config/
│   └── tokens.json                 # Token watchlist (26 active)
├── data/
│   ├── opportunities.json          # Final output (dashboard source)
│   ├── latest.json                 # Current prices
│   ├── solanatracker_cache.json    # Persistent cache (static data)
│   ├── solanatracker_data.json     # Latest fetch (dynamic data)
│   └── ...
├── dashboard/
│   └── index.html                  # Surge.sh dashboard
├── database/
│   └── supabase_client.py          # Database interface
└── ARCHITECTURE.md                 # This file
```

---

## API Keys & Secrets

| Secret | Purpose | Source |
|--------|---------|--------|
| `SOLANATRACKER_API_KEY` | Security & holder data | solanatracker.io |
| `SUPABASE_URL` | Database endpoint | Supabase |
| `SUPABASE_SERVICE_KEY` | Database write access | Supabase |
| `HELIUS_API_KEY` | Backup metadata | Helius |
| `TELEGRAM_BOT_TOKEN` | Notifications | Telegram |
| `TELEGRAM_CHAT_ID` | Alert destination | Telegram |

---

## Cost Analysis

### Monthly Costs (Free Tier Only)

| Service | Free Tier | Usage | Status |
|---------|-----------|-------|--------|
| DexScreener | Unlimited | ~720 requests/day | ✅ Within limits |
| SolanaTracker | 1000 credits | ~130 credits/month | ✅ Within limits |
| Helius | 100K credits | ~111 credits/day | ✅ Within limits |
| Supabase | 500MB / 2GB | ~50MB / ~200GB | ✅ Within limits |
| Surge.sh | Unlimited | Static files | ✅ Free |
| GitHub Actions | 2000 min | ~1440 min/month | ✅ Within limits |
| **Total** | | | **$0/month** |

---

## Performance Metrics

### Pipeline Timing

| Step | Duration | Notes |
|------|----------|-------|
| SolanaTracker Agent | 2-5 min | Depends on cache hits |
| Research (DexScreener) | 4-5 min | 26 tokens × 6s |
| Thinking (Scoring) | 1 min | Calculations |
| Merge & Save | 1 min | Write files |
| Git Commit | 1 min | Push to GitHub |
| **Total** | **~10-13 min** | |

### Dashboard Load

| Component | Time | Source |
|-----------|------|--------|
| Initial Data | ~2s | GitHub Raw CDN |
| Price Updates | Every 30s | DexScreener API |
| Full Refresh | Every 5 min | GitHub Raw CDN |

---

## Future Improvements

### Planned Enhancements

1. **Real-time Updates**
   - Supabase Realtime for instant score updates
   - WebSocket connection for price streaming

2. **Historical Analysis**
   - Track holder growth over time
   - Correlate security scores with price performance

3. **Alert Enhancements**
   - Security score changes
   - LP burn events
   - Sudden holder growth

4. **Machine Learning**
   - Predict score accuracy based on historical data
   - Identify patterns in successful tokens

---

## Troubleshooting

### Common Issues

**Issue:** SolanaTracker data not showing on dashboard
**Cause:** Pipeline overwrites opportunities.json after merge
**Fix:** Merge now integrated into collect_and_score.py save_files()

**Issue:** Rate limiting on SolanaTracker
**Cause:** Too frequent API calls
**Fix:** Optimized agent with 2-day cache for dynamic data

**Issue:** High credit usage
**Cause:** Fetching all data every run
**Fix:** Separate static (once) vs dynamic (every 2 days) data

---

## References

- **Dashboard:** https://squirmyscreener.surge.sh
- **GitHub:** https://github.com/jdhuman2021-web/weirdo-tracker
- **SolanaTracker Docs:** https://docs.solanatracker.io
- **DexScreener API:** https://docs.dexscreener.com

---

*Architecture v2.0 - Optimized for 1000 SolanaTracker credits/month*