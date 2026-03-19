# Supported Scan Message Formats

## Rick Burp Bot Format (Primary)

```
[💊] [https://pump.fun/{contract}] [TokenName] [MCAP/X%] $SYMBOL [🔼]
🌐 Solana @ Pump
💰 USD: {price}
💎 FDV: {fdv_current} ⇨ {fdv_peak} [{days}d]
💦 Liq: {liquidity} [x{multiplier}]
📊 Vol: {volume} ⋅ Age: {age}d
📈 1H: {volume_1h} ⋅ {change}% 🅑 {buys} Ⓢ {sells}

[👥] TH: [{holder_dist}] [{pct}%]
[🤝] Total: {holders} ⋅ avg {avg_age} old
🌱 Fresh 1D: {fresh_1d}% ⋅ 7D: {fresh_7d}%
[💹] Chart: [DEX]⋅[DEF]
🧰 More: [🫧] [🎨] [💪] [🌍] [🐦]

{contract_address}
[MAE]⋅[BAN]⋅[BNK]⋅[PDR]⋅[BLO]⋅[STB]⋅[NEO]
[TRO]⋅[TRT]⋅[GMG]⋅[PHO]⋅[AXI]⋅[EXP]⋅[TW]

🏆 [{user}] @ {mcap}⋅{time} 👀 {views}
```

## Extracted Fields

| Field | Regex Pattern | Example |
|-------|--------------|---------|
| Contract | `[A-Za-z0-9]{40,50}pump` | `CXjctbA7ENQgZf1FnMLJJUGKp92gAJdMcyEhXeZppump` |
| Symbol | `\$[A-Z]+` | `$HAMSTER` |
| Price | `USD:\s*([0-9.]+)` | `0.0001605` |
| Market Cap | `FDV:\s*([0-9.KM]+)` | `160K` |
| Liquidity | `Liq:\s*([0-9.KM]+)` | `17K` |
| Volume | `Vol:\s*([0-9.KM]+)` | `366K` |
| Age | `Age:\s*(\d+)d` | `1d` |
| Holders | `Total:\s*([0-9.KM]+)` | `492` |
| Fresh 1D | `Fresh 1D:\s*(\d+)%` | `4%` |
| Fresh 7D | `Fresh 7D:\s*(\d+)%` | `11%` |
| 1H Change | `1H:.*⋅\s*([+-]?[0-9.]+)%` | `-13.3%` |

## Manual Input Format

Just paste the contract address:
```
G9ivB7K41a4G8m1k4QdxxN4L5eGKL7Mr12S26B85pump
```

Will be added with placeholder data, updated on next API fetch.

## Discord Screenshot Format

When user sends screenshot of scan:
- OCR not supported
- Ask user to copy/paste text or forward message
- Or manually input contract address