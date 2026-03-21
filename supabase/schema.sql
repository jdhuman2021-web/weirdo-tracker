-- Weirdo Tracker Database Schema (Supabase)
-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tokens table (master list)
CREATE TABLE IF NOT EXISTS tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol TEXT NOT NULL,
    name TEXT,
    address TEXT UNIQUE NOT NULL,
    chain TEXT DEFAULT 'SOL',
    added_date DATE,
    source TEXT,
    notes TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on address for fast lookups
CREATE INDEX IF NOT EXISTS idx_tokens_address ON tokens(address);
CREATE INDEX IF NOT EXISTS idx_tokens_status ON tokens(status);

-- Price snapshots (historical data)
CREATE TABLE IF NOT EXISTS price_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token_id UUID REFERENCES tokens(id) ON DELETE CASCADE,
    token_address TEXT NOT NULL,
    price_usd DECIMAL(20, 10),
    market_cap DECIMAL(20, 2),
    volume_24h DECIMAL(20, 2),
    liquidity_usd DECIMAL(20, 2),
    price_change_1h DECIMAL(10, 4),
    price_change_24h DECIMAL(10, 4),
    holder_count INTEGER DEFAULT 0,
    age_hours INTEGER,
    score INTEGER,
    signal TEXT,
    captured_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_snapshots_token ON price_snapshots(token_address);
CREATE INDEX IF NOT EXISTS idx_snapshots_captured ON price_snapshots(captured_at DESC);
CREATE INDEX IF NOT EXISTS idx_snapshots_score ON price_snapshots(score DESC);

-- Whale activity tracking
CREATE TABLE IF NOT EXISTS whale_activity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token_address TEXT NOT NULL,
    whale_address TEXT NOT NULL,
    whale_name TEXT,
    action TEXT CHECK(action IN ('buy', 'sell')),
    amount_usd DECIMAL(20, 2),
    tx_hash TEXT,
    captured_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_whale_token ON whale_activity(token_address);
CREATE INDEX IF NOT EXISTS idx_whale_captured ON whale_activity(captured_at DESC);

-- Alerts log
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token_address TEXT NOT NULL,
    alert_type TEXT,
    message TEXT,
    score INTEGER,
    threshold_type TEXT,
    acknowledged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at DESC);

-- Pipeline runs (audit trail)
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_timestamp TIMESTAMPTZ DEFAULT NOW(),
    tokens_fetched INTEGER,
    opportunities_found INTEGER,
    alerts_sent INTEGER,
    status TEXT,
    error_message TEXT,
    duration_seconds DECIMAL(10, 2)
);

-- Enable Row Level Security (RLS)
ALTER TABLE tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE price_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE whale_activity ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_runs ENABLE ROW LEVEL SECURITY;

-- Create policies for public read (anon key)
CREATE POLICY "Public read access" ON tokens FOR SELECT USING (true);
CREATE POLICY "Public read access" ON price_snapshots FOR SELECT USING (true);
CREATE POLICY "Public read access" ON whale_activity FOR SELECT USING (true);
CREATE POLICY "Public read access" ON alerts FOR SELECT USING (true);
CREATE POLICY "Public read access" ON pipeline_runs FOR SELECT USING (true);

-- Create a function to get latest prices (view)
CREATE OR REPLACE VIEW latest_prices AS
SELECT 
    t.symbol,
    t.name,
    t.address,
    t.status,
    ps.price_usd,
    ps.market_cap,
    ps.volume_24h,
    ps.price_change_24h,
    ps.score,
    ps.signal,
    ps.captured_at
FROM tokens t
JOIN price_snapshots ps ON t.address = ps.token_address
WHERE t.status = 'active'
  AND ps.id IN (
    SELECT MAX(id) FROM price_snapshots GROUP BY token_address
  )
ORDER BY ps.score DESC;

-- Create function to get token stats
CREATE OR REPLACE VIEW token_stats AS
SELECT 
    t.symbol,
    t.address,
    COUNT(ps.id) as snapshot_count,
    MIN(ps.captured_at) as first_tracked,
    MAX(ps.captured_at) as last_tracked,
    AVG(ps.score) as avg_score
FROM tokens t
LEFT JOIN price_snapshots ps ON t.address = ps.token_address
WHERE t.status = 'active'
GROUP BY t.address, t.symbol;

-- Create function to upsert token (insert or update)
CREATE OR REPLACE FUNCTION upsert_token(
    p_symbol TEXT,
    p_name TEXT,
    p_address TEXT,
    p_chain TEXT DEFAULT 'SOL',
    p_source TEXT DEFAULT NULL,
    p_notes TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_id UUID;
BEGIN
    INSERT INTO tokens (symbol, name, address, chain, source, notes)
    VALUES (p_symbol, p_name, p_address, p_chain, p_source, p_notes)
    ON CONFLICT (address) 
    DO UPDATE SET 
        symbol = EXCLUDED.symbol,
        name = EXCLUDED.name,
        updated_at = NOW()
    RETURNING id INTO v_id;
    
    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

-- Create function to insert price snapshot
CREATE OR REPLACE FUNCTION insert_snapshot(
    p_token_address TEXT,
    p_price_usd DECIMAL,
    p_market_cap DECIMAL,
    p_volume_24h DECIMAL,
    p_liquidity_usd DECIMAL,
    p_price_change_1h DECIMAL,
    p_price_change_24h DECIMAL,
    p_holder_count INTEGER,
    p_age_hours INTEGER,
    p_score INTEGER,
    p_signal TEXT
) RETURNS UUID AS $$
DECLARE
    v_id UUID;
BEGIN
    INSERT INTO price_snapshots (
        token_address, price_usd, market_cap, volume_24h, liquidity_usd,
        price_change_1h, price_change_24h, holder_count, age_hours, score, signal
    ) VALUES (
        p_token_address, p_price_usd, p_market_cap, p_volume_24h, p_liquidity_usd,
        p_price_change_1h, p_price_change_24h, p_holder_count, p_age_hours, p_score, p_signal
    )
    RETURNING id INTO v_id;
    
    RETURN v_id;
END;
$$ LANGUAGE plpgsql;