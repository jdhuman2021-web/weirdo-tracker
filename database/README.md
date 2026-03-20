# 🗄️ Weirdo Tracker Database

SQLite database for persistent storage of token data, price history, whale activity, and alerts.

---

## 📁 Files

| File | Purpose |
|------|---------|
| `tracker.db` | SQLite database (auto-created) |
| `schema.sql` | Table definitions |
| `db_init.py` | Initialize database |
| `db_queries.py` | Query functions (Python) |
| `migrate_json.py` | Import JSON data |

---

## 🚀 Quick Start

### 1. Initialize Database
```powershell
cd database
python db_init.py
```

### 2. Migrate Existing Data
```powershell
python migrate_json.py
```

### 3. Query Data (Python)
```python
from db_queries import get_all_tokens, get_latest_prices, get_token_summary

# Get all tokens
tokens = get_all_tokens()

# Get latest prices
prices = get_latest_prices(limit=20)

# Get summary stats
summary = get_token_summary()
print(summary)
```

---

## 📊 Schema Overview

### Tables

| Table | Purpose |
|-------|---------|
| `tokens` | Master token list |
| `price_snapshots` | Historical price data |
| `whale_activity` | Whale buy/sell logs |
| `alerts` | Alert history |
| `pipeline_runs` | Pipeline audit trail |

### Views

| View | Purpose |
|------|---------|
| `latest_prices` | Current price for each token |
| `token_stats` | Aggregated stats per token |

---

## 🔧 Integration with Pipeline

Update your GitHub Actions workflow to:
1. Write to database after fetching data
2. Query historical data for scoring
3. Log pipeline runs

### Example (Python Agent)
```python
from database.db_queries import add_price_snapshot, log_pipeline_run

# After fetching token data:
add_price_snapshot(
    token_address="NV2RYH954cTJ3ckFUpvfqaQXU4ARqqDH3562nFSpump",
    price_usd=0.01396,
    market_cap=13966358,
    volume_24h=1613220,
    liquidity_usd=722810,
    price_change_1h=-7.46,
    price_change_24h=-7.62,
    holder_count=1234,
    age_hours=1042,
    score=44,
    signal="WATCH"
)

# At end of pipeline:
log_pipeline_run(
    tokens_fetched=37,
    opportunities_found=7,
    alerts_sent=2,
    status="success",
    duration_seconds=180
)
```

---

## 📈 Benefits Over JSON

| Feature | JSON | SQLite |
|---------|------|--------|
| Historical queries | ❌ Manual parsing | ✅ SQL queries |
| Data integrity | ❌ No validation | ✅ Foreign keys |
| Concurrent access | ❌ Race conditions | ✅ Transactions |
| Analytics | ❌ Custom code | ✅ Aggregations |
| Backup | ✅ Copy file | ✅ Copy file |
| Size | ✅ Small | ✅ Compact |

---

## 🔍 Useful Queries

### Price history for a token
```sql
SELECT * FROM price_snapshots 
WHERE token_address = 'NV2RYH954cTJ3ckFUpvfqaQXU4ARqqDH3562nFSpump'
ORDER BY captured_at DESC
LIMIT 24;
```

### Average score by token age
```sql
SELECT 
    CASE WHEN age_hours < 24 THEN 'Fresh (<24h)'
         WHEN age_hours < 168 THEN 'Week-old (1-7d)'
         ELSE 'Established' END as age_bracket,
    AVG(score) as avg_score,
    COUNT(*) as count
FROM price_snapshots
GROUP BY age_bracket;
```

### Whale activity summary
```sql
SELECT 
    whale_name,
    COUNT(*) as total_actions,
    SUM(CASE WHEN action='buy' THEN 1 ELSE 0 END) as buys,
    SUM(CASE WHEN action='sell' THEN 1 ELSE 0 END) as sells
FROM whale_activity
GROUP BY whale_name
ORDER BY total_actions DESC;
```

---

## 🛠️ Tools

### SQLite CLI (built-in)
```powershell
sqlite3 tracker.db
> .tables
> SELECT * FROM tokens LIMIT 5;
> .quit
```

### DB Browser for SQLite (GUI)
Download: https://sqlitebrowser.org/

---

## 📝 Notes

- Database file is in `database/` folder
- Back up by copying `tracker.db`
- Schema changes require migration scripts
- All times are UTC
