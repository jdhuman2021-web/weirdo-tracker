<!-- Squirmy Screener - Real-Time Dashboard -->
<!-- Polls DexScreener every 30 seconds for live prices -->
<!-- Full data refresh every 5 minutes from GitHub -->
<!-- Supabase Realtime for instant score updates -->

<script>
// Real-time price polling
let priceUpdateInterval;

async function fetchRealTimePrices() {
    if (!currentData?.opportunities) return;
    
    const tokens = currentData.opportunities;
    const addresses = tokens.slice(0, 30).map(t => t.address);
    
    try {
        const url = `https://api.dexscreener.com/latest/dex/tokens/${addresses.join(',')}`;
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.pairs) {
            tokens.forEach(token => {
                const pair = data.pairs.find(p => 
                    p.baseToken?.address?.toLowerCase() === token.address?.toLowerCase()
                );
                if (pair) {
                    token.price_usd = parseFloat(pair.priceUsd || 0);
                    token.price_change_1h = parseFloat(pair.priceChange?.h1 || 0);
                    token.price_change_24h = parseFloat(pair.priceChange?.h24 || 0);
                    token.volume_24h = parseFloat(pair.volume?.h24 || 0);
                    token.liquidity_usd = parseFloat(pair.liquidity?.usd || 0);
                }
            });
            
            renderTokenList();
            updateStats();
            console.log('Updated prices at', new Date().toLocaleTimeString());
        }
    } catch (e) {
        console.error('Price update error:', e);
    }
}

// Start real-time updates
function startRealTime() {
    fetchRealTimePrices();
    priceUpdateInterval = setInterval(fetchRealTimePrices, 30000);
}

// Initialize
loadData().then(() => {
    startRealTime();
});
setInterval(loadData, 300000);
</script>