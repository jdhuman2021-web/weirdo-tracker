# Weirdo Portfolio Tracker - Periodic Checks

## When to Run
Every 30 minutes during active hours (08:00-23:00 UTC)

## Checklist

### 1. Load Tracker Data
- Read solana_tracker.json
- Get list of active contracts

### 2. Fetch Updates (Free APIs)
For each contract:
- [ ] DexScreener: Get latest price, volume, liquidity
- [ ] Calculate price change % (1h, 24h)
- [ ] Calculate volume vs average
- [ ] Check holder count changes

### 3. Check Thresholds
Alert if ANY of:
- [ ] Price change >20% (1h) or >50% (24h)
- [ ] Volume spike >2x average
- [ ] Holder growth >10% (24h)
- [ ] Liquidity drain >30%

### 4. Update History
- Append current data to each contract's history array
- Keep last 7 days of data

### 5. Report Findings
- Send alert for any threshold breaches
- Include: Contract, Symbol, Metric, Change %, Link

## API Endpoints (Free)
- DexScreener: https://api.dexscreener.com/latest/dex/tokens/{contract}

## Notes
- Respect rate limits: Max 10-20 calls per minute