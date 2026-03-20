-- Database Migration: Add Status Column
-- Run: python db_migrate.py

-- Add status column to tokens table
ALTER TABLE tokens ADD COLUMN status TEXT DEFAULT 'active';

-- Add status column to price_snapshots (for reference)
ALTER TABLE price_snapshots ADD COLUMN token_status TEXT DEFAULT 'active';

-- Create index for filtering
CREATE INDEX IF NOT EXISTS idx_tokens_status ON tokens(status);

-- Update existing tokens to 'active'
UPDATE tokens SET status = 'active' WHERE status IS NULL;

-- Create view for active tokens only
CREATE VIEW IF NOT EXISTS active_tokens AS
SELECT * FROM tokens WHERE status = 'active';

-- Create view for active latest prices
CREATE VIEW IF NOT EXISTS active_latest_prices AS
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
WHERE t.status = 'active'
  AND ps.id IN (
    SELECT MAX(id) FROM price_snapshots GROUP BY token_address
);
