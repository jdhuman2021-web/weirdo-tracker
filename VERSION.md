# Weirdo Portfolio Tracker - Version History

## Current Version: v1.0.0

### v1.0.0 (2026-03-19)
**Commit:** `ead6a9a`

#### Features
- **29 Tokens** tracked with live DexScreener data
- **Portfolio Tab** with sortable columns:
  - Token, Price, 12h Change, 24h Change, 1h Change
  - Liquidity, Market Cap, Status
- **Scanner Tab** with "Track Token" feature
  - Paste contract address → generates command for AI assistant
  - Auto-validation for Solana addresses
  - Clipboard integration
- **Whale Tracker** with 87 wallet profiles
- **Dashboard** with portfolio overview and charts
- **Accumulation Scanner** with configurable thresholds
- **Alert System** with audio notifications

#### Data
- Real-time prices from DexScreener API
- 12h, 24h, 1h change percentages
- Liquidity and market cap values
- Token metadata (names, symbols, contracts)

#### Files
- `unified-tracker.html` - Main tracker application
- `token-data.js` - Token data backup
- `whale_wallets.json` - 87 whale wallet database
- `birdeye-whale-links.html` - Quick wallet access links
- Supporting tools (PowerShell scripts, standalone trackers)

---

## Version Control

This project uses Git for version control.

### Key Commits
```
ead6a9a - v1.0.0: Initial tracker release with 29 tokens
0db376a - Organize workspace
88f1867 - Initial commit
```

### Tracking Changes
To see what changed:
```bash
git log --oneline
git diff HEAD~1
git show [commit-hash]
```

### Rolling Back
If you need to revert to a previous version:
```bash
# See previous versions
git log --oneline

# Revert to specific version
git checkout [commit-hash] -- unified-tracker.html

# Or reset to previous commit (dangerous - loses changes)
git reset --hard HEAD~1
```

---

## Future Versions

### Planned for v1.1.0
- [ ] Auto-refresh from DexScreener API
- [ ] Price alerts via Telegram
- [ ] Export to PDF report
- [ ] Mobile-responsive improvements

### Planned for v1.2.0
- [ ] Real-time WebSocket price updates
- [ ] Portfolio profit/loss tracking
- [ ] Historical price charts
- [ ] Token comparison tool

---

Last Updated: 2026-03-19 22:41 UTC
