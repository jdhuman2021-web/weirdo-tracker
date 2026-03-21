-- Migration 004: Token Metadata & Market Context
-- Run this in Supabase SQL Editor

-- ============================================
-- TOKEN METADATA ENHANCEMENTS
-- ============================================

-- Add new columns to tokens table
ALTER TABLE tokens ADD COLUMN IF NOT EXISTS decimals INTEGER DEFAULT 9;
ALTER TABLE tokens ADD COLUMN IF NOT EXISTS total_supply BIGINT;
ALTER TABLE ADD COLUMN IF NOT EXISTS creator_address TEXT;
ALTER TABLE tokens ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE tokens ADD COLUMN IF NOT EXISTS launch_date DATE;
ALTER TABLE tokens ADD COLUMN IF NOT EXISTS launch_platform TEXT;
-- 'pump.fun', 'raydium', 'meteora', 'orca', etc.
ALTER TABLE tokens ADD COLUMN IF NOT EXISTS social_links JSONB DEFAULT '{}';
-- {"twitter": "url", "telegram": "url", "website": "url", "discord": "url"}
ALTER TABLE tokens ADD COLUMN IF NOT EXISTS contract_type TEXT DEFAULT 'standard';
-- 'standard', 'mintable', 'burnable', 'taxed', 'rebase'
ALTER TABLE tokens ADD COLUMN IF NOT EXISTS tax_rate DECIMAL(5, 2) DEFAULT 0;
ALTER TABLE tokens ADD COLUMN IF NOT EXISTS max_transaction_usd DECIMAL(20, 2);
ALTER TABLE tokens ADD COLUMN IF NOT EXISTS metadata_uri TEXT;

-- ============================================
-- TOKEN VERIFICATION
-- ============================================

CREATE TABLE IF NOT EXISTS token_verification (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token_address TEXT NOT NULL REFERENCES tokens(address) ON DELETE CASCADE,
    verification_type TEXT NOT NULL,
    -- 'contract_audit', 'team_doxxed', 'liquidity_locked', 'ownership_renounced'
    verification_status TEXT DEFAULT 'pending',
    -- 'pending', 'verified', 'failed'
    verification_date DATE,
    verifier_name TEXT,
    -- Audit firm or verification service
    report_url TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_verification_token ON token_verification(token_address);
CREATE INDEX IF NOT EXISTS idx_verification_status ON token_verification(verification_status);

-- ============================================
-- TOKEN HOLDINGS DISTRIBUTION
-- ============================================

CREATE TABLE IF NOT EXISTS holder_distribution (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token_address TEXT NOT NULL,
    captured_at TIMESTAMPTZ DEFAULT NOW(),
    -- Top holders
    top_10_holders_pct DECIMAL(10, 4),
    -- % held by top 10 wallets
    top_100_holders_pct DECIMAL(10, 4),
    -- % held by top 100 wallets
    top_holder_pct DECIMAL(10, 4),
    -- Largest single holder %
    -- Distribution metrics
    gini_coefficient DECIMAL(5, 4),
    -- Wealth inequality measure
    holder_count INTEGER,
    active_holders_7d INTEGER,
    -- Holders who traded in last 7 days
    whale_holders INTEGER
    -- Holders owning >1% of supply
);

CREATE INDEX IF NOT EXISTS idx_holder_dist_token ON holder_distribution(token_address);
CREATE INDEX IF NOT EXISTS idx_holder_dist_captured ON holder_distribution(captured_at DESC);

-- ============================================
-- TOKEN LAUNCHES
-- Track newly launched tokens
-- ============================================

CREATE TABLE IF NOT EXISTS token_launches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token_address TEXT NOT NULL,
    launch_date DATE,
    launch_platform TEXT,
    -- 'pump.fun', 'raydium', 'meteora'
    initial_liquidity_usd DECIMAL(20, 2),
    initial_market_cap DECIMAL(20, 2),
    initial_holders INTEGER,
    creator_address TEXT,
    -- First price and metrics
    first_price DECIMAL(20, 10),
    first_snapshot_id UUID REFERENCES price_snapshots(id),
    -- Launch success metrics
    price_at_24h DECIMAL(20, 10),
    price_at_7d DECIMAL(20, 10),
    price_at_30d DECIMAL(20, 10),
    survived BOOLEAN,
    -- True if still active after 30 days
    rug_pull_detected BOOLEAN DEFAULT FALSE,
    rug_pull_date DATE,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_launches_token ON token_launches(token_address);
CREATE INDEX IF NOT EXISTS idx_launches_date ON token_launches(launch_date DESC);

-- ============================================
-- TOKEN SOCIAL LINKS
-- ============================================

CREATE TABLE IF NOT EXISTS token_socials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token_address TEXT NOT NULL REFERENCES tokens(address) ON DELETE CASCADE,
    platform TEXT NOT NULL,
    -- 'twitter', 'telegram', 'discord', 'website', 'medium', 'reddit'
    url TEXT NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    followers_count INTEGER,
    last_checked DATE,
    notes TEXT,
    UNIQUE(token_address, platform)
);

CREATE INDEX IF NOT EXISTS idx_socials_token ON token_socials(token_address);

-- ============================================
-- USEFUL VIEWS
-- ============================================

-- Token with full metadata
CREATE OR REPLACE VIEW token_full AS
SELECT 
    t.*,
    tv.verification_status,
    tv.verification_type as audit_status,
    hd.top_10_holders_pct,
    hd.top_holder_pct,
    hd.gini_coefficient,
    hd.holder_count,
    hd.active_holders_7d,
    tl.launch_platform,
    tl.initial_liquidity_usd,
    tl.survived,
    tl.rug_pull_detected,
    jsonb_object_agg(ts.platform, ts.url) as social_links
FROM tokens t
LEFT JOIN token_verification tv ON t.address = tv.token_address
LEFT JOIN holder_distribution hd ON t.address = hd.token_address
    AND hd.captured_at = (
        SELECT MAX(captured_at) FROM holder_distribution WHERE token_address = t.address
    )
LEFT JOIN token_launches tl ON t.address = tl.token_address
LEFT JOIN token_socials ts ON t.address = ts.token_address
GROUP BY t.address, tv.verification_status, tv.verification_type,
         hd.top_10_holders_pct, hd.top_holder_pct, hd.gini_coefficient,
         hd.holder_count, hd.active_holders_7d,
         tl.launch_platform, tl.initial_liquidity_usd, tl.survived, tl.rug_pull_detected;

-- ============================================
-- TRIGGER TO UPDATE timestamps
-- ============================================

CREATE OR REPLACE FUNCTION update_token_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tokens_updated ON tokens;
CREATE TRIGGER tokens_updated
    BEFORE UPDATE ON tokens
    FOR EACH ROW EXECUTE FUNCTION update_token_timestamp();

-- ============================================
-- CONSTRAINTS
-- ============================================

ALTER TABLE tokens ADD CONSTRAINT valid_status 
    CHECK (status IN ('active', 'dead', 'paused', 'watching'));

ALTER TABLE tokens ADD CONSTRAINT valid_chain
    CHECK (chain IN ('SOL', 'ETH', 'BSC', 'ARB', 'MATIC', 'AVAX', 'FTM', 'OTHER'));

ALTER TABLE token_verification ADD CONSTRAINT valid_verification_type
    CHECK (verification_type IN ('contract_audit', 'team_doxxed', 'liquidity_locked', 'ownership_renounced', 'kyc'));

ALTER TABLE holder_distribution ADD CONSTRAINT valid_gini
    CHECK (gini_coefficient >= 0 AND gini_coefficient <= 1);

-- ============================================
-- INDEXES FOR COMMON QUERIES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_tokens_status_chain ON tokens(status, chain);
CREATE INDEX IF NOT EXISTS idx_tokens_launch_date ON tokens(added_date);
CREATE INDEX IF NOT EXISTS idx_tokens_verified ON tokens(is_verified) WHERE is_verified = TRUE;