-- Migration 003: Score History & Performance Tracking
-- Run this in Supabase SQL Editor

-- ============================================
-- SCORE HISTORY
-- Track WHY scores change over time
-- ============================================

CREATE TABLE IF NOT EXISTS score_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token_address TEXT NOT NULL,
    score INTEGER NOT NULL,
    signal TEXT NOT NULL,
    -- Factors breakdown (why this score?)
    factors JSONB DEFAULT '{}',
    -- Example: {
    --   "price_position": 25,
    --   "volume_ratio": 30,
    --   "holder_growth": 15,
    --   "liquidity": 12,
    --   "age": 5,
    --   "whale_bonus": 15
    -- }
    -- Risk factors
    risk_factors JSONB DEFAULT '[]',
    -- ["Crashed -50%", "Low liquidity"]
    -- Opportunities
    opportunities JSONB DEFAULT '[]',
    -- ["Volume spike 10x", "Whale accumulation"]
    -- Context
    market_context JSONB DEFAULT '{}',
    -- {"btc_trend": "up", "fear_greed_index": 65}
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    -- Link to price snapshot
    snapshot_id UUID REFERENCES price_snapshots(id)
);

CREATE INDEX IF NOT EXISTS idx_score_token ON score_history(token_address);
CREATE INDEX IF NOT NOT EXISTS idx_score_captured ON score_history(calculated_at DESC);
CREATE INDEX IF NOT EXISTS idx_score_value ON score_history(score DESC);

-- ============================================
-- TOKEN PERFORMANCE
-- Track historical performance for backtesting
-- ============================================

CREATE TABLE IF NOT EXISTS token_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token_address TEXT NOT NULL,
    captured_at TIMESTAMPTZ DEFAULT NOW(),
    -- Price metrics
    price_usd DECIMAL(20, 10),
    price_change_1h DECIMAL(10, 4),
    price_change_24h DECIMAL(10, 4),
    price_change_7d DECIMAL(10, 4),
    -- Volume metrics
    volume_24h DECIMAL(20, 2),
    volume_ratio DECIMAL(10, 2),
    -- Market metrics
    market_cap DECIMAL(20, 2),
    liquidity_usd DECIMAL(20, 2),
    fdv DECIMAL(20, 2),
    -- Holder metrics
    holder_count INTEGER,
    holder_change_24h DECIMAL(10, 4),
    holder_change_7d DECIMAL(10, 4),
    -- Score metrics
    score INTEGER,
    signal TEXT,
    -- Calculated fields
    price_vs_score DECIMAL(5, 2),
    -- Correlation between price and score
    volatility_24h DECIMAL(10, 4),
    -- Price volatility
    trend TEXT
    -- 'up', 'down', 'sideways', 'volatile'
);

CREATE INDEX IF NOT EXISTS idx_perf_token ON token_performance(token_address);
CREATE INDEX IF NOT EXISTS idx_perf_captured ON token_performance(captured_at DESC);

-- ============================================
-- MARKET CONTEXT
-- Track overall market for correlation
-- ============================================

CREATE TABLE IF NOT EXISTS market_context (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    captured_at TIMESTAMPTZ DEFAULT NOW(),
    -- Major coins
    btc_price_usd DECIMAL(20, 2),
    btc_change_24h DECIMAL(10, 4),
    eth_price_usd DECIMAL(20, 2),
    eth_change_24h DECIMAL(10, 4),
    sol_price_usd DECIMAL(20, 2),
    sol_change_24h DECIMAL(10, 4),
    -- Market metrics
    total_market_cap DECIMAL(20, 2),
    total_volume_24h DECIMAL(20, 2),
    btc_dominance DECIMAL(5, 2),
    -- Sentiment
    fear_greed_index INTEGER,
    -- 0-100
    -- Narrative tracking
    dominant_narrative TEXT,
    -- 'ai', 'meme', 'defi', 'gaming', 'layer2'
    narrative_strength DECIMAL(5, 2)
    -- 0-1 confidence
);

CREATE INDEX IF NOT EXISTS idx_market_captured ON market_context(captured_at DESC);

-- ============================================
-- SOCIAL METRICS
-- Track social signals
-- ============================================

CREATE TABLE IF NOT EXISTS social_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token_address TEXT NOT NULL,
    captured_at TIMESTAMPTZ DEFAULT NOW(),
    -- Twitter
    twitter_followers INTEGER,
    twitter_mentions_24h INTEGER,
    twitter_sentiment DECIMAL(3, 2),
    -- -1 to 1
    -- Telegram
    telegram_members INTEGER,
    telegram_active_24h INTEGER,
    telegram_messages_24h INTEGER,
    -- Discord
    discord_members INTEGER,
    discord_online INTEGER,
    -- General
    social_score DECIMAL(5, 2),
    -- Computed 0-100
    viral_coefficient DECIMAL(5, 2),
    -- Growth velocity
    hype_level TEXT
    -- 'low', 'medium', 'high', 'extreme'
);

CREATE INDEX IF NOT EXISTS idx_social_token ON social_metrics(token_address);
CREATE INDEX IF NOT EXISTS idx_social_captured ON social_metrics(captured_at DESC);

-- ============================================
-- VIEWS FOR ANALYTICS
-- ============================================

-- Score progression over time
CREATE OR REPLACE VIEW score_progression AS
SELECT 
    sh.token_address,
    t.symbol,
    sh.calculated_at,
    sh.score,
    sh.signal,
    sh.factors->>'price_position' as price_factor,
    sh.factors->>'volume_ratio' as volume_factor,
    sh.factors->>'whale_bonus' as whale_factor,
    LAG(sh.score) OVER (PARTITION BY sh.token_address ORDER BY sh.calculated_at) as prev_score,
    LAG(sh.score) OVER (PARTITION BY sh.token_address ORDER BY sh.calculated_at) - sh.score as score_change
FROM score_history sh
JOIN tokens t ON sh.token_address = t.address
ORDER BY sh.calculated_at DESC;

-- Token performance summary
CREATE OR REPLACE VIEW token_performance_summary AS
SELECT 
    t.symbol,
    t.address,
    COUNT(tp.id) as data_points,
    AVG(tp.score) as avg_score,
    MAX(tp.score) as max_score,
    MIN(tp.score) as min_score,
    AVG(tp.price_change_24h) as avg_24h_change,
    STDDEV(tp.price_change_24h) as volatility,
    CORR(tp.score, tp.price_change_24h) as score_price_correlation
FROM tokens t
LEFT JOIN token_performance tp ON t.address = tp.token_address
GROUP BY t.address, t.symbol;

-- Whale activity summary
CREATE OR REPLACE VIEW whale_activity_summary AS
SELECT 
    wp.address,
    wp.name,
    wp.tags,
    COUNT(DISTINCT wa.token_address) as tokens_traded,
    SUM(wa.amount_usd) FILTER (WHERE wa.action = 'buy') as total_buys_usd,
    SUM(wa.amount_usd) FILTER (WHERE wa.action = 'sell') as total_sells_usd,
    MAX(wa.captured_at) as last_activity,
    COUNT(*) as total_actions
FROM whale_profiles wp
LEFT JOIN whale_activity wa ON wp.address = wa.whale_address
GROUP BY wp.address, wp.name, wp.tags
ORDER BY total_actions DESC;

-- ============================================
-- FUNCTIONS FOR BACKTESTING
-- ============================================

-- Calculate win rate for a scoring threshold
CREATE OR REPLACE FUNCTION calculate_win_rate(
    min_score INTEGER,
    days_back INTEGER DEFAULT 7
)
RETURNS TABLE (
    token_address TEXT,
    symbol TEXT,
    entry_score INTEGER,
    entry_price DECIMAL,
    exit_price DECIMAL,
    price_change_pct DECIMAL,
    is_win BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sh.token_address,
        t.symbol,
        sh.score::INTEGER as entry_score,
        sh.price_usd as entry_price,
        tp.price_usd as exit_price,
        ((tp.price_usd - sh.price_usd) / sh.price_usd * 100)::DECIMAL as price_change_pct,
        (tp.price_usd > sh.price_usd) as is_win
    FROM score_history sh
    JOIN tokens t ON sh.token_address = t.address
    JOIN token_performance tp ON sh.token_address = tp.token_address
        AND tp.captured_at = (
            SELECT MAX(captured_at) 
            FROM token_performance 
            WHERE token_address = sh.token_address
        )
    WHERE sh.score >= min_score
        AND sh.calculated_at > NOW() - (days_back || ' days')::INTERVAL
    ORDER BY sh.calculated_at DESC;
END;
$$ LANGUAGE plpgsql;