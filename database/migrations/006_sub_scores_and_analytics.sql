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
CREATE INDEX IF NOT EXISTS idx_score_history_scored_at ON score_history(scored_at DESC);
CREATE INDEX IF NOT EXISTS idx_score_history_velocity ON score_history(score_velocity DESC);

-- ============================================
-- View: Signal Attribution Ready
-- Joins score_history with price outcomes for correlation analysis
-- ============================================

CREATE OR REPLACE VIEW signal_attribution_ready AS
SELECT 
    sh.id,
    t.symbol,
    sh.scored_at,
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
    sh.price_at_score,
    sh.price_after_24h,
    sh.price_after_7d,
    CASE 
        WHEN sh.price_after_24h IS NOT NULL AND sh.price_at_score > 0
        THEN ((sh.price_after_24h - sh.price_at_score) / sh.price_at_score * 100)
        ELSE NULL
    END AS return_24h_pct,
    CASE 
        WHEN sh.price_after_7d IS NOT NULL AND sh.price_at_score > 0
        THEN ((sh.price_after_7d - sh.price_at_score) / sh.price_at_score * 100)
        ELSE NULL
    END AS return_7d_pct
FROM score_history sh
JOIN tokens t ON t.id = sh.token_id
WHERE sh.price_at_score > 0;

-- ============================================
-- View: Watchlist Health Score (Idea #4)
-- ============================================

CREATE OR REPLACE VIEW watchlist_health_score AS
SELECT
    DATE_TRUNC('hour', scored_at) AS hour,
    COUNT(*) FILTER (WHERE recommendation IN ('STRONG_BUY','BUY')) AS bullish_count,
    COUNT(*) FILTER (WHERE recommendation = 'SPECULATIVE') AS speculative_count,
    COUNT(*) FILTER (WHERE recommendation IN ('WATCH','AVOID')) AS bearish_count,
    COUNT(*) AS total_tokens,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE recommendation IN ('STRONG_BUY','BUY','SPECULATIVE'))
        / COUNT(*), 1
    ) AS health_score
FROM score_history
WHERE scored_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', scored_at)
ORDER BY hour DESC;

-- ============================================
-- View: Volume Acceleration Calculation (Idea #1)
-- ============================================

CREATE OR REPLACE VIEW token_volume_stats AS
SELECT
    t.symbol,
    t.id AS token_id,
    (
        SELECT AVG(volume_24h) 
        FROM price_snapshots 
        WHERE token_id = t.id 
        AND timestamp >= NOW() - INTERVAL '7 days'
    ) AS vol_7d_avg,
    (
        SELECT volume_24h 
        FROM price_snapshots 
        WHERE token_id = t.id 
        ORDER BY timestamp DESC 
        LIMIT 1
    ) AS vol_current,
    ROUND(
        (
            SELECT volume_24h 
            FROM price_snapshots 
            WHERE token_id = t.id 
            ORDER BY timestamp DESC 
            LIMIT 1
        ) / NULLIF((
            SELECT AVG(volume_24h) 
            FROM price_snapshots 
            WHERE token_id = t.id 
            AND timestamp >= NOW() - INTERVAL '7 days'
        ), 0), 2
    ) AS vol_acceleration
FROM tokens t
WHERE t.status = 'active';

-- ============================================
-- Success message
-- ============================================

SELECT 'Migration 006 completed - Sub-scores and quick-win analytics ready!' as status;