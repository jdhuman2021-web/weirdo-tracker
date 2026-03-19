# Free API Endpoints for Solana Data

## DexScreener (Free, No Key Required)

### Get Token Data
```
GET https://api.dexscreener.com/latest/dex/tokens/{contract_address}
```

Returns:
- Price (USD)
- Market Cap
- Liquidity
- Volume (24h, 6h, 1h)
- Price changes
- Social links

### Get Specific Pair
```
GET https://api.dexscreener.com/latest/dex/pairs/solana/{pair_address}
```

## CoinGecko (Free Tier)

### Get Token Data
```
GET https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={coin_id}
```

Rate limit: 10-30 calls/minute

### Search Token
```
GET https://api.coingecko.com/api/v3/search?query={token_name}
```

## Helius (Free Tier - 500 requests/day)

### Get Token Holders
```
POST https://mainnet.helius-rpc.com/?api-key={API_KEY}
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "getTokenAccountsByOwner",
  "params": ["{owner_address}", {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"}]
}
```

## Jupiter (Free)

### Get Price
```
GET https://price.jup.ag/v4/price?ids={contract_address}
```

Returns current price in USD.

## Birdeye (Free Tier)

### Get Token Overview
```
GET https://public-api.birdeye.so/public/token?address={contract_address}
```

Requires API key in header: `X-API-KEY: {your_key}`

## Rate Limiting Best Practices

1. Cache results for 30-60 seconds
2. Batch requests when possible
3. Prioritize active contracts
4. Skip contracts with <10K liquidity
5. Use DexScreener as primary (most reliable)