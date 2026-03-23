-- Migration 007: Opportunity Snapshots for Trend Analysis
-- Store complete snapshots of all opportunities to identify market trends

-- ============================================
-- OPPORTUNITY SNAPSHOTS
-- Complete market view at each pipeline run
-- ============================================

CREATE TABLE IF NOT EXISTS opportunity_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID REFERENCES pipeline_runs(id),
    captured_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Market summary
    total_tokens INTEGER,
    tokens_scored INTEGER,
    avg_score DECIMAL(5, 2),
    median_score DECIMAL(5, 2),
    
    -- Signal distribution
    strong_buy_count INTEGER DEFAULT 0,
    buy_count INTEGER DEFAULT 0,
    speculative_count INTEGER DEFAULT 0,
    watch_count INTEGER DEFAULT 0,
    avoid_count INTEGER DEFAULT 0,
    
    -- Market health metrics
    health_score DECIMAL(5, 2),  -- % of tokens in BUY+SPECULATIVE
    bullish_ratio DECIMAL(5, 2), -- BUY / (BUY + AVOID)
    
    -- Volume metrics
    total_volume_24h DECIMAL(20, 2),
    avg_volume_acceleration DECIMAL(10, 2),
    volume_spike_count INTEGER,  -- tokens with vol_acceleration > 5
    
    -- Top performers (store as JSON array)
    top_5_opportunities JSONB DEFAULT '[]',
    -- [
    --   {"symbol": "PUNCH", "score": 85, "signal": "BUY", "price_usd": 0.011},
    --   ...
    -- ]
    
    -- Market regime
    market_regime TEXT DEFAULT 'neutral',
    -- 'risk_on', 'risk_off', 'neutral', 'volatile'
    
    -- Metadata
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_opp_snap_captured ON opportunity_snapshots(captured_at DESC);
CREATE INDEX IF NOT EXISTS idx_opp_snap_health ON opportunity_snapshots(health_score DESC);
CREATE INDEX IF NOT EXISTS idx_opp_snap_regime ON opportunity_snapshots(market_regime);

-- ============================================
-- View: Daily Opportunity Trends
-- ============================================

CREATE OR REPLACE VIEW daily_opportunity_trends AS
SELECT
    DATE_TRUNC('day', captured_at) AS day,
    COUNT(*) AS snapshot_count,
    AVG(health_score) AS avg_health,
    AVG(strong_buy_count) AS avg_strong_buys,
    AVG(buy_count) AS avg_buys,
    AVG(avoid_count) AS avg_avoids,
    AVG(total_volume_24h) AS avg_total_volume,
    MAX(top_5_opportunities) AS best_opportunities
FROM opportunity_snapshots
WHERE captured_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', captured_at)
ORDER BY day DESC;

-- ============================================
-- View: Market Regime History
-- ============================================

CREATE OR REPLACE VIEW market_regime_history AS
SELECT
    captured_at,
    market_regime,
    health_score,
    bullish_ratio,
    strong_buy_count + buy_count AS total_buys,
    speculative_count,
    watch_count + avoid_count AS total_bears,
    CASE
        WHEN health_score > 60 THEN 'RISK_ON'
        WHEN health_score < 30 THEN 'RISK_OFF'
        ELSE 'NEUTRAL'
    END AS regime_label
FROM opportunity_snapshots
WHERE captured_at >= NOW() - INTERVAL '7 days'
ORDER BY captured_at DESC;

-- ============================================
-- View: Score Distribution Trends
-- ============================================

CREATE OR REPLACE VIEW score_distribution_trends AS
SELECT
    DATE_TRUNC('hour', captured_at) AS hour,
    AVG(strong_buy_count) AS strong_buys,
    AVG(buy_count) AS buys,
    AVG(speculative_count) AS speculative,
    AVG(watch_count) AS watch,
    AVG(avoid_count) AS avoids,
    AVG(total_tokens) AS total_tokens
FROM opportunity_snapshots
WHERE captured_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', captured_at)
ORDER BY hour DESC;

-- ============================================
-- Success message
-- ============================================

SELECT 'Migration 007 completed - Opportunity snapshots ready for trend analysis!' as status;