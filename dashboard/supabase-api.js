// Supabase API Client for Dashboard
// Add this to the dashboard to query historical data

const SUPABASE_URL = 'https://zrghgmnizofduovxaqpb.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_HRMPreVF4qhjOiSM7jthTQ_674MU986';

// Fetch latest prices from Supabase
async function fetchLatestPrices(limit = 50) {
    const response = await fetch(`${SUPABASE_URL}/rest/v1/rpc/latest_prices?limit=${limit}`, {
        headers: {
            'apikey': SUPABASE_ANON_KEY,
            'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
        }
    });
    
    if (!response.ok) {
        throw new Error('Failed to fetch from Supabase');
    }
    
    return await response.json();
}

// Fetch price history for a token
async function fetchPriceHistory(tokenAddress, hours = 24) {
    const response = await fetch(
        `${SUPABASE_URL}/rest/v1/price_snapshots?token_address=eq.${tokenAddress}&captured_at=gte.now().minus('${hours} hours')&order=captured_at.desc`,
        {
            headers: {
                'apikey': SUPABASE_ANON_KEY,
                'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
            }
        }
    );
    
    if (!response.ok) {
        throw new Error('Failed to fetch history');
    }
    
    return await response.json();
}

// Fetch token stats
async function fetchTokenStats() {
    const response = await fetch(`${SUPABASE_URL}/rest/v1/rpc/token_stats`, {
        headers: {
            'apikey': SUPABASE_ANON_KEY,
            'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
        }
    });
    
    return await response.json();
}