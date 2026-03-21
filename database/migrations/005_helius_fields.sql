-- Migration 005: Add Helius fields for holder and wallet tracking
-- Run this in Supabase SQL Editor

-- ============================================
-- Add Helius-specific fields to tokens
-- ============================================

ALTER TABLE tokens ADD COLUMN IF NOT EXISTS pump_fun_address TEXT;
ALTER TABLE tokens ADD COLUMN IF NOT EXISTS launch_platform TEXT DEFAULT 'unknown';
ALTER TABLE tokens ADD COLUMN IF NOT EXISTS creator_address TEXT;
ALTER TABLE tokens ADD COLUMN IF NOT EXISTS holder_count INTEGER;
ALTER TABLE tokens ADD COLUMN IF NOT EXISTS fresh_wallet_count INTEGER DEFAULT 0;
ALTER TABLE tokens ADD COLUMN IF NOT EXISTS decimals INTEGER;

-- ============================================
-- Add indexes for new fields
-- ============================================

CREATE INDEX IF NOT EXISTS idx_tokens_launch_platform ON tokens(launch_platform);
CREATE INDEX IF NOT EXISTS idx_tokens_creator ON tokens(creator_address);
CREATE INDEX IF NOT EXISTS idx_tokens_holder_count ON tokens(holder_count DESC);

-- ============================================
-- Add fields to token_launches
-- ============================================

ALTER TABLE token_launches ADD COLUMN IF NOT EXISTS pump_fun_address TEXT;

CREATE INDEX IF NOT EXISTS idx_launches_platform ON token_launches(launch_platform);
CREATE INDEX IF NOT EXISTS idx_launches_creator ON token_launches(creator_address);

-- ============================================
-- Fresh wallet tracking
-- ============================================

CREATE TABLE IF NOT EXISTS fresh_wallets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    wallet_address TEXT NOT NULL,
    token_address TEXT NOT NULL REFERENCES tokens(address),
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    wallet_age_hours INTEGER,
    balance DECIMAL(30, 9),
    is_fresh BOOLEAN DEFAULT TRUE,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_fresh_wallets_token ON fresh_wallets(token_address);
CREATE INDEX IF NOT EXISTS idx_fresh_wallets_wallet ON fresh_wallets(wallet_address);
CREATE INDEX IF NOT EXISTS idx_fresh_wallets_age ON fresh_wallets(wallet_age_hours);

-- ============================================
-- View for fresh wallet stats
-- ============================================

CREATE OR REPLACE VIEW fresh_wallet_summary AS
SELECT 
    token_address,
    COUNT(*) as fresh_wallet_count,
    SUM(balance) as total_fresh_balance,
    AVG(wallet_age_hours) as avg_wallet_age
FROM fresh_wallets
WHERE is_fresh = TRUE
GROUP BY token_address;

-- ============================================
-- Success message
-- ============================================

SELECT 'Migration 005 completed - Helius fields added!' as status;