-- Migration 004 Fixed: Token Metadata
-- Run this in Supabase SQL Editor

-- ============================================
-- Add columns to tokens table (only if not exists)
-- ============================================

-- Check and add each column individually
DO $$
BEGIN
    -- decimals
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'tokens' AND column_name = 'decimals') THEN
        ALTER TABLE tokens ADD COLUMN decimals INTEGER DEFAULT 9;
    END IF;
    
    -- total_supply
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'tokens' AND column_name = 'total_supply') THEN
        ALTER TABLE tokens ADD COLUMN total_supply BIGINT;
    END IF;
    
    -- creator_address
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'tokens' AND column_name = 'creator_address') THEN
        ALTER TABLE tokens ADD COLUMN creator_address TEXT;
    END IF;
    
    -- is_verified
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'tokens' AND column_name = 'is_verified') THEN
        ALTER TABLE tokens ADD COLUMN is_verified BOOLEAN DEFAULT FALSE;
    END IF;
    
    -- launch_date
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'tokens' AND column_name = 'launch_date') THEN
        ALTER TABLE tokens ADD COLUMN launch_date DATE;
    END IF;
    
    -- launch_platform
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'tokens' AND column_name = 'launch_platform') THEN
        ALTER TABLE tokens ADD COLUMN launch_platform TEXT;
    END IF;
    
    -- social_links
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'tokens' AND column_name = 'social_links') THEN
        ALTER TABLE tokens ADD COLUMN social_links JSONB DEFAULT '{}';
    END IF;
    
    -- contract_type
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'tokens' AND column_name = 'contract_type') THEN
        ALTER TABLE tokens ADD COLUMN contract_type TEXT DEFAULT 'standard';
    END IF;
    
    -- tax_rate
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'tokens' AND column_name = 'tax_rate') THEN
        ALTER TABLE tokens ADD COLUMN tax_rate DECIMAL(5, 2) DEFAULT 0;
    END IF;
    
    -- max_transaction_usd
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'tokens' AND column_name = 'max_transaction_usd') THEN
        ALTER TABLE tokens ADD COLUMN max_transaction_usd DECIMAL(20, 2);
    END IF;
    
    -- metadata_uri
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'tokens' AND column_name = 'metadata_uri') THEN
        ALTER TABLE tokens ADD COLUMN metadata_uri TEXT;
    END IF;
END $$;

-- ============================================
-- Token Verification
-- ============================================

CREATE TABLE IF NOT EXISTS token_verification (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token_address TEXT NOT NULL,
    verification_type TEXT NOT NULL,
    verification_status TEXT DEFAULT 'pending',
    verification_date DATE,
    verifier_name TEXT,
    report_url TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_verification_token ON token_verification(token_address);

-- ============================================
-- Holder Distribution
-- ============================================

CREATE TABLE IF NOT EXISTS holder_distribution (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token_address TEXT NOT NULL,
    captured_at TIMESTAMPTZ DEFAULT NOW(),
    top_10_holders_pct DECIMAL(10, 4),
    top_100_holders_pct DECIMAL(10, 4),
    top_holder_pct DECIMAL(10, 4),
    gini_coefficient DECIMAL(5, 4),
    holder_count INTEGER,
    active_holders_7d INTEGER,
    whale_holders INTEGER
);

CREATE INDEX IF NOT EXISTS idx_holder_dist_token ON holder_distribution(token_address);
CREATE INDEX IF NOT EXISTS idx_holder_dist_captured ON holder_distribution(captured_at DESC);

-- ============================================
-- Token Launches
-- ============================================

CREATE TABLE IF NOT EXISTS token_launches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token_address TEXT NOT NULL,
    launch_date DATE,
    launch_platform TEXT,
    initial_liquidity_usd DECIMAL(20, 2),
    initial_market_cap DECIMAL(20, 2),
    initial_holders INTEGER,
    creator_address TEXT,
    first_price DECIMAL(20, 10),
    price_at_24h DECIMAL(20, 10),
    price_at_7d DECIMAL(20, 10),
    price_at_30d DECIMAL(20, 10),
    survived BOOLEAN,
    rug_pull_detected BOOLEAN DEFAULT FALSE,
    rug_pull_date DATE,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_launches_token ON token_launches(token_address);
CREATE INDEX IF NOT EXISTS idx_launches_date ON token_launches(launch_date DESC);

-- ============================================
-- Token Socials
-- ============================================

CREATE TABLE IF NOT EXISTS token_socials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token_address TEXT NOT NULL,
    platform TEXT NOT NULL,
    url TEXT NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    followers_count INTEGER,
    last_checked DATE,
    notes TEXT,
    UNIQUE(token_address, platform)
);

CREATE INDEX IF NOT EXISTS idx_socials_token ON token_socials(token_address);

-- ============================================
-- Constraints (use DO blocks to avoid errors if already exists)
-- ============================================

DO $$
BEGIN
    -- Add valid_status constraint if not exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'valid_status'
    ) THEN
        ALTER TABLE tokens ADD CONSTRAINT valid_status 
            CHECK (status IN ('active', 'dead', 'paused', 'watching'));
    END IF;
    
    -- Add valid_chain constraint if not exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'valid_chain'
    ) THEN
        ALTER TABLE tokens ADD CONSTRAINT valid_chain
            CHECK (chain IN ('SOL', 'ETH', 'BSC', 'ARB', 'MATIC', 'AVAX', 'FTM', 'OTHER'));
    END IF;
END $$;

-- ============================================
-- Indexes
-- ============================================

CREATE INDEX IF NOT EXISTS idx_tokens_status_chain ON tokens(status, chain);
CREATE INDEX IF NOT EXISTS idx_tokens_launch_date ON tokens(added_date);
CREATE INDEX IF NOT EXISTS idx_tokens_verified ON tokens(is_verified) WHERE is_verified = TRUE;

-- ============================================
-- Token Full View (Drop first to avoid duplicates)
-- ============================================

DROP VIEW IF EXISTS token_full CASCADE;

CREATE VIEW token_full AS
SELECT 
    t.id,
    t.symbol,
    t.name,
    t.address,
    t.chain,
    t.status,
    t.added_date,
    t.source,
    t.notes,
    t.decimals,
    t.total_supply,
    t.creator_address,
    t.is_verified,
    t.launch_date,
    t.launch_platform,
    t.social_links,
    t.contract_type,
    t.tax_rate,
    t.created_at,
    t.updated_at,
    tv.verification_status,
    tv.verification_type as audit_status,
    hd.top_10_holders_pct,
    hd.top_holder_pct,
    hd.gini_coefficient,
    hd.holder_count,
    hd.active_holders_7d,
    tl.initial_liquidity_usd,
    tl.survived,
    tl.rug_pull_detected
FROM tokens t
LEFT JOIN token_verification tv ON t.address = tv.token_address
LEFT JOIN holder_distribution hd ON t.address = hd.token_address
    AND hd.captured_at = (
        SELECT MAX(captured_at) FROM holder_distribution WHERE token_address = t.address
    )
LEFT JOIN token_launches tl ON t.address = tl.token_address;

-- ============================================
-- Success message
-- ============================================

SELECT 'Migration 004 completed successfully!' as status;