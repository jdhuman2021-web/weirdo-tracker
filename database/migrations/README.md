# Database Schema v2.0 - Migration Summary

## Overview

This migration adds comprehensive tracking for the Squirmy Screener platform.

## Migration Files

| File | Purpose | Tables |
|------|---------|--------|
| `001_add_status_column.sql` | Status field + views | tokens, price_snapshots |
| `002_whale_intelligence.sql` | Whale tracking | whale_profiles, whale_wallets, whale_patterns |
| `003_score_history.sql` | Performance tracking | score_history, token_performance, market_context, social_metrics |
| `004_token_metadata.sql` | Token details | token_verification, holder_distribution, token_launches, token_socials |

## New Tables

### Whale Intelligence
- `whale_profiles` - Track 87 whale wallets with metadata
- `whale_wallets` - Link multiple wallets to single whale
- `whale_patterns` - Track recurring whale behaviors

### Score History
- `score_history` - WHY scores change over time
- `token_performance` - Historical performance metrics
- `market_context` - BTC/ETH/SOL prices + fear/greed index
- `social_metrics` - Twitter/Telegram/Discord followers

### Token Metadata
- `token_verification` - Contract audits, team doxxed, liquidity locked
- `holder_distribution` - Top holder %, Gini coefficient
- `token_launches` - Launch platform, initial metrics, rug pull detection
- `token_socials` - Social media links

## Key Features

### 1. Whale Intelligence
```sql
-- Track whale patterns
SELECT * FROM whale_patterns WHERE pattern_type = 'accumulation';

-- Active whales in last 24h
SELECT * FROM active_whales;

-- Whale summary with stats
SELECT * FROM whale_summary WHERE tracked = TRUE;
```

### 2. Score History
```sql
-- Why did this token get score 75?
SELECT factors, risk_factors FROM score_history 
WHERE token_address = 'xxx' ORDER BY calculated_at DESC LIMIT 1;

-- Score progression over time
SELECT * FROM score_progression WHERE token_address = 'xxx';

-- Backtest win rate
SELECT * FROM calculate_win_rate(min_score := 70, days_back := 7);
```

### 3. Market Context
```sql
-- Correlation with market
SELECT * FROM market_context ORDER BY captured_at DESC LIMIT 1;

-- Fear/Greed impact on scores
SELECT mc.fear_greed_index, AVG(sh.score) 
FROM market_context mc 
JOIN score_history sh ON DATE(mc.captured_at) = DATE(sh.calculated_at)
GROUP BY mc.fear_greed_index;
```

### 4. Token Metadata
```sql
-- Full token info with verification
SELECT * FROM token_full WHERE address = 'xxx';

-- Rug pull risk
SELECT address, rug_pull_detected, top_holder_pct, gini_coefficient 
FROM holder_distribution 
WHERE top_holder_pct > 50 OR gini_coefficient > 0.8;
```

## Usage

### Run Migrations
```bash
cd database
python run_migrations.py
```

### In Supabase
1. Go to SQL Editor
2. Open each migration file
3. Click Run

## Data Growth Estimates

| Table | Daily Rows | Monthly | Yearly |
|-------|-----------|---------|--------|
| `price_snapshots` | 1,776 | 53K | 649K |
| `score_history` | 1,776 | 53K | 649K |
| `token_performance` | 1,776 | 53K | 649K |
| `social_metrics` | 1,776 | 53K | 649K |
| `market_context` | 48 | 1.4K | 17K |
| `whale_activity` | 100-500 | 3K-15K | 36K-180K |
| **Total** | ~7K | ~215K | ~2.6M |

## Indexes Added

- `idx_whale_*` - Fast whale queries
- `idx_score_*` - Score history lookups
- `idx_perf_*` - Performance tracking
- `idx_social_*` - Social metrics
- `idx_market_captured` - Market context

## Views Created

- `whale_summary` - Whale stats with wallet counts
- `active_whales` - Whales active in last 24h
- `score_progression` - Score changes over time
- `token_performance_summary` - Aggregated performance
- `token_full` - Token with all metadata