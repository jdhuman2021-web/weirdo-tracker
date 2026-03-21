-- Migration 002: Enhanced Whale Intelligence
-- Run this in Supabase SQL Editor

-- ============================================
-- WHALE PROFILES
-- Track the 87 whale wallets with metadata
-- ============================================

CREATE TABLE IF NOT EXISTS whale_profiles (
    address TEXT PRIMARY KEY,
    name TEXT,
    nickname TEXT,
    tags JSONB DEFAULT '[]',
    -- ['whale', 'insider', 'early_investor', 'dev', 'known_entity']
    tracked BOOLEAN DEFAULT TRUE,
    priority TEXT DEFAULT 'medium',
    -- 'high', 'medium', 'low'
    notes TEXT,
    first_seen TIMESTAMPTZ,
    last_active TIMESTAMPTZ,
    total_buy_volume_usd DECIMAL(20, 2) DEFAULT 0,
    total_sell_volume_usd DECIMAL(20, 2) DEFAULT 0,
    win_rate DECIMAL(5, 2),
    -- Historical win rate (0-100)
    avg_holding_time_hours INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_whale_profiles_tracked ON whale_profiles(tracked) WHERE tracked = TRUE;
CREATE INDEX IF NOT EXISTS idx_whale_profiles_priority ON whale_profiles(priority);

-- ============================================
-- WHALE WALLETS
-- Link multiple wallets to a single whale profile
-- ============================================

CREATE TABLE IF NOT EXISTS whale_wallets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    whale_address TEXT NOT NULL REFERENCES whale_profiles(address) ON DELETE CASCADE,
    wallet_address TEXT NOT NULL,
    wallet_name TEXT,
    wallet_type TEXT DEFAULT 'primary',
    -- 'primary', 'secondary', 'trading', 'holding'
    added_date DATE,
    notes TEXT,
    UNIQUE(whale_address, wallet_address)
);

CREATE INDEX IF NOT EXISTS idx_whale_wallets_whale ON whale_wallets(whale_address);
CREATE INDEX IF NOT EXISTS idx_whale_wallets_wallet ON whale_wallets(wallet_address);

-- ============================================
-- WHALE ACTIVITY ENHANCED
-- ============================================

-- Add more fields to existing whale_activity table
ALTER TABLE whale_activity ADD COLUMN IF NOT EXISTS price_at_action DECIMAL(20, 10);
ALTER TABLE whale_activity ADD COLUMN IF NOT EXISTS portfolio_impact DECIMAL(5, 2);
ALTER TABLE whale_activity ADD COLUMN IF NOT EXISTS detected_method TEXT;
-- 'on-chain', 'birdeye', 'manual'
ALTER TABLE whale_activity ADD COLUMN IF NOT EXISTS confidence_score DECIMAL(3, 2) DEFAULT 1.0;
-- 0-1 confidence in detection

-- ============================================
-- WHALE PATTERNS
-- Track recurring whale behaviors
-- ============================================

CREATE TABLE IF NOT EXISTS whale_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    whale_address TEXT NOT NULL REFERENCES whale_profiles(address),
    pattern_type TEXT NOT NULL,
    -- 'accumulation', 'distribution', 'pump_dump', 'swing_trade'
    token_address TEXT,
    pattern_frequency INTEGER DEFAULT 1,
    -- How many times this pattern occurred
    success_rate DECIMAL(5, 2),
    -- How often pattern led to profit
    avg_price_change DECIMAL(10, 4),
    -- Average price change after pattern
    first_occurrence TIMESTAMPTZ,
    last_occurrence TIMESTAMPTZ,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_whale_patterns_whale ON whale_patterns(whale_address);
CREATE INDEX IF NOT EXISTS idx_whale_patterns_type ON whale_patterns(pattern_type);

-- ============================================
-- POPULATE FROM EXISTING WHALE WALLETS
-- ============================================

-- This assumes you have whale_wallets.json with your 87 wallets
-- We'll create a function to import them

CREATE OR REPLACE FUNCTION import_whale_wallets(wallets JSONB)
RETURNS INTEGER AS $$
DECLARE
    wallet RECORD;
    imported_count INTEGER := 0;
BEGIN
    FOR wallet IN SELECT * FROM jsonb_array_elements(wallets)
    LOOP
        -- Create whale profile if not exists
        INSERT INTO whale_profiles (address, name, tracked)
        VALUES (
            wallet->>'address',
            COALESCE(wallet->>'name', 'Unknown Whale'),
            TRUE
        )
        ON CONFLICT (address) DO NOTHING;
        
        -- Link wallet
        INSERT INTO whale_wallets (whale_address, wallet_address, wallet_name, wallet_type)
        VALUES (
            wallet->>'address',
            wallet->>'address',
            wallet->>'name',
            COALESCE(wallet->>'type', 'primary')
        )
        ON CONFLICT (whale_address, wallet_address) DO NOTHING;
        
        imported_count := imported_count + 1;
    END LOOP;
    
    RETURN imported_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- VIEWS FOR WHALE INTELLIGENCE
-- ============================================

CREATE OR REPLACE VIEW whale_summary AS
SELECT 
    wp.address,
    wp.name,
    wp.nickname,
    wp.tags,
    wp.tracked,
    wp.priority,
    COUNT(DISTINCT ww.wallet_address) as wallet_count,
    COALESCE(SUM(wa.amount_usd) FILTER (WHERE wa.action = 'buy'), 0) as total_buy_usd,
    COALESCE(SUM(wa.amount_usd) FILTER (WHERE wa.action = 'sell'), 0) as total_sell_usd,
    COUNT(DISTINCT wa.token_address) as tokens_traded,
    MAX(wa.captured_at) as last_activity
FROM whale_profiles wp
LEFT JOIN whale_wallets ww ON wp.address = ww.whale_address
LEFT JOIN whale_activity wa ON wp.address = wa.whale_address
GROUP BY wp.address, wp.name, wp.nickname, wp.tags, wp.tracked, wp.priority;

-- Active whales in last 24h
CREATE OR REPLACE VIEW active_whales AS
SELECT 
    wp.address,
    wp.name,
    wp.tags,
    COUNT(*) as recent_actions,
    SUM(wa.amount_usd) as total_volume,
    array_agg(DISTINCT wa.token_address) as tokens_active
FROM whale_profiles wp
JOIN whale_activity wa ON wp.address = wa.whale_address
WHERE wa.captured_at > NOW() - INTERVAL '24 hours'
GROUP BY wp.address, wp.name, wp.tags
ORDER BY total_volume DESC;