-- Migration 006: Add sub-score fields for signal attribution analysis
-- This enables Idea #9: Signal Attribution Backtest
-- Run this in Supabase SQL Editor

-- ============================================
-- Add sub-score fields to score_history
-- ============================================

ALTER TABLE score_history ADD COLUMN IF NOT EXISTS vol_score INTEGER DEFAULT 0;
ALTER TABLE score_history ADD COLUMN IF NOT EXISTS whale_score INTEGER DEFAULT 0;
ALTER TABLE score_history ADD COLUMN IF NOT EXISTS security_score INTEGER DEFAULT 0;
ALTER TABLE score_history ADD COLUMN IF NOT EXISTS holder_score INTEGER DEFAULT 0;
ALTER TABLE score_history ADD COLUMN IF NOT EXISTS momentum_score INTEGER DEFAULT 0;
ALTER TABLE score_history ADD COLUMN IF NOT EXISTS social_score INTEGER DEFAULT 0;
ALTER TABLE score_history ADD COLUMN IF NOT EXISTS age_score INTEGER DEFAULT 0;

-- ============================================
-- Add quick-win analysis fields
-- ============================================

ALTER TABLE score_history ADD COLUMN IF NOT EXISTS vol_acceleration DECIMAL(10,2) DEFAULT 0;
ALTER TABLE score_history ADD COLUMN IF NOT EXISTS price_momentum_slope DECIMAL(10,4) DEFAULT 0;
ALTER TABLE score_history ADD COLUMN IF NOT EXISTS score_velocity INTEGER DEFAULT 0;
ALTER TABLE score_history ADD COLUMN IF NOT EXISTS score_velocity_label TEXT DEFAULT 'STABLE';

-- ============================================
-- Add token-level aggregations
-- ============================================

-- 7-day volume average (for acceleration calculation)
ALTER TABLE tokens ADD COLUMN IF NOT EXISTS vol_7d_avg DECIMAL(20,2) DEFAULT 0;
ALTER TABLE tokens ADD COLUMN IF NOT EXISTS last_vol_update TIMESTAMPTZ;

-- ============================================
-- Indexes for performance
-- ============================================

CREATE INDEX IF NOT EXISTS idx_score_history_vol_score ON score_history(vol_score DESC);
CREATE INDEX IF NOT EXISTS idx_score_history_security_score ON score_history(security_score DESC);
CREATE INDEX IF NOT EXISTS idx_score_history_whale_score ON score_history(whale_score DESC);
CREATE INDEX IF NOT EXISTS idx_score_history_scored_at ON score_history(calculated_at DESC);
CREATE INDEX IF NOT EXISTS idx_score_history_velocity ON score_history(score_velocity DESC);

-- ============================================
-- View: Signal Attribution Ready
-- Joins score_history with price outcomes for correlation analysis
-- ============================================

CREATE OR REPLACE VIEW signal_attribution_ready AS
SELECT 
    sh.id,
    t.symbol,
    sh.calculated_at AS scored_at,
    sh.score,
    sh.vol_score,
    sh.whale_score,
    sh.security_score,
    sh.holder_score,
    sh.momentum_score,
    sh.social_score,
    sh.age_score,
    sh.vol_acceleration,
    sh.price_momentum_slope,
    sh.score_velocity,
    -- Placeholder fields for attribution analysis
    0 AS price_at_score,
    0 AS price_after_24h,
    0 AS price_after_7d,
    0 AS return_24h_pct,
    0 AS return_7d_pct
FROM score_history sh
JOIN tokens t ON t.address = sh.token_address;

-- ============================================
-- View: Watchlist Health Score (Idea #4)
-- ============================================

CREATE OR REPLACE VIEW watchlist_health_score AS
SELECT
    DATE_TRUNC('hour', calculated_at) AS hour,
    COUNT(*) FILTER (WHERE signal IN ('STRONG_BUY','BUY')) AS bullish_count,
    COUNT(*) FILTER (WHERE signal = 'SPECULATIVE') AS speculative_count,
    COUNT(*) FILTER (WHERE signal IN ('WATCH','AVOID')) AS bearish_count,
    COUNT(*) AS total_tokens,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE signal IN ('STRONG_BUY','BUY','SPECULATIVE'))
        / COUNT(*), 1
    ) AS health_score
FROM score_history
WHERE calculated_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', calculated_at)
ORDER BY hour DESC;

-- ============================================
-- View: Volume Acceleration Calculation (Idea #1)
-- Simplified version - uses direct token_address
-- ============================================

-- NOTE: This view requires price_snapshots to have token_address
-- If your schema uses token_id, adjust accordingly

-- For now, skip this view and implement in Python
-- CREATE OR REPLACE VIEW token_volume_stats AS ...

-- ============================================
-- Success message
-- ============================================

SELECT 'Migration 006 completed - Sub-scores ready!\nNote: Volume acceleration view skipped - implement in Python agent' as status;