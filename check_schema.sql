-- DIAGNOSTIC: Check your schema before running migration 006
-- Run this first to see what columns exist

-- Check price_snapshots columns
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'price_snapshots' 
ORDER BY ordinal_position;

-- Check tokens columns  
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'tokens'
ORDER BY ordinal_position;

-- Check score_history columns
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'score_history'
ORDER BY ordinal_position;