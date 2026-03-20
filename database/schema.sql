-- Weirdo Tracker Database Schema
-- SQLite format

-- Tokens table (master list)
CREATE TABLE IF NOT EXISTS tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    name TEXT,
    address TEXT UNIQUE NOT NULL,
    chain TEXT DEFAULT 'SOL',
    added_date TEXT,
    source TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Price snapshots (historical data)
CREATE TABLE IF NOT EXISTS price_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_address TEXT NOT NULL,
    price_usd REAL,
    market_cap REAL,
    volume_24h REAL,
    liquidity_usd REAL,
    price_change_1h REAL,
    price_change_24h REAL,
    holder_count INTEGER,
    age_hours INTEGER,
    score INTEGER,
    signal TEXT,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (token_address) REFERENCES tokens(address)
);

-- Whale activity tracking
CREATE TABLE IF NOT EXISTS whale_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_address TEXT NOT NULL,
    whale_address TEXT NOT NULL,
    whale_name TEXT,
    action TEXT CHECK(action IN ('buy', 'sell')),
    amount_usd REAL,
    tx_hash TEXT,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (token_address) REFERENCES tokens(address)
);

-- Alerts log
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_address TEXT NOT NULL,
    alert_type TEXT,
    message TEXT,
    score INTEGER,
    threshold_type TEXT,
    acknowledged INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (token_address) REFERENCES tokens(address)
);

-- Pipeline runs (audit trail)
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tokens_fetched INTEGER,
    opportunities_found INTEGER,
    alerts_sent INTEGER,
    status TEXT,
    error_message TEXT,
    duration_seconds REAL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_price_token ON price_snapshots(token_address);
CREATE INDEX IF NOT EXISTS idx_price_captured ON price_snapshots(captured_at);
CREATE INDEX IF NOT EXISTS idx_whale_token ON whale_activity(token_address);
CREATE INDEX IF NOT EXISTS idx_whale_captured ON whale_activity(captured_at);
CREATE INDEX IF NOT EXISTS idx_alerts_token ON alerts(token_address);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at);

-- Views for common queries
CREATE VIEW IF NOT EXISTS latest_prices AS
SELECT 
    t.symbol,
    t.name,
    t.address,
    ps.price_usd,
    ps.market_cap,
    ps.volume_24h,
    ps.price_change_24h,
    ps.score,
    ps.signal,
    ps.captured_at
FROM tokens t
JOIN price_snapshots ps ON t.address = ps.token_address
WHERE ps.id IN (
    SELECT MAX(id) FROM price_snapshots GROUP BY token_address
);

CREATE VIEW IF NOT EXISTS token_stats AS
SELECT 
    t.symbol,
    t.address,
    COUNT(ps.id) as snapshot_count,
    MIN(ps.captured_at) as first_tracked,
    MAX(ps.captured_at) as last_tracked,
    AVG(ps.score) as avg_score
FROM tokens t
LEFT JOIN price_snapshots ps ON t.address = ps.token_address
GROUP BY t.address;
