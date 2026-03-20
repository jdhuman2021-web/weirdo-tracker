# GitHub Actions Setup Guide

## Overview

The Weirdo Tracker runs automatically every 15 minutes via GitHub Actions.

## How It Works

```
Schedule (15 min) → Checkout → Run Agents → Commit → Dashboard Updates
```

**Agents executed in order:**
1. **Research Agent** - Fetches DexScreener data
2. **Thinking Agent** - Calculates scores 0-100
3. **Alert Agent** - Checks thresholds, sends Telegram

## Setup Instructions

### Step 1: Push to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

### Step 2: Configure Secrets (Optional)

For Telegram alerts, add these secrets in GitHub repo settings:

**Go to:** Settings → Secrets and variables → Actions → New repository secret

| Secret Name | Value |
|-------------|-------|
| `TELEGRAM_BOT_TOKEN` | Your bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | Your chat ID (use @userinfobot) |

### Step 3: Verify Workflow

1. Go to **Actions** tab in your repo
2. Click **"Weirdo Tracker - Data Pipeline"**
3. Click **"Run workflow"** button
4. Check that it completes successfully

## Workflow Features

### Automatic Triggers
- **Every 15 minutes** via cron schedule
- **Manual trigger** with custom reason
- **Push trigger** on workflow changes

### Data Flow
1. Reads `config/tokens.json` for token list
2. Fetches live data from DexScreener
3. Saves results to `data/` folder
4. Commits changes back to repo
5. Dashboard reads from `data/opportunities.json`

### Error Handling
- Caches API responses
- Uploads artifacts for debugging
- Telegram notification on failure
- Skips commit if no changes

## Monitoring

### View Runs
- GitHub Actions tab → "Weirdo Tracker"
- Shows: Success/failure, duration, trigger

### View Logs
- Click any run → "collect-data" job
- Expand steps to see agent output

### Data Files
```
data/
├── opportunities.json    # Scored opportunities
├── alerts.json         # Triggered alerts
└── latest.json         # Raw market data
```

## Costs

**GitHub Actions Free Tier:**
- 2,000 minutes/month
- This workflow: ~2 minutes/run × 96 runs/day = ~3,000 min/month

**Note:** May exceed free tier at 15-min intervals. Options:
1. Change to `*/30 * * * *` (30 min)
2. Use self-hosted runner
3. Pay $0.008/minute overage

## Troubleshooting

### Workflow not running?
- Check Actions tab → enable workflows
- Verify cron syntax
- Check branch name matches

### Data not updating?
- Check `data/` folder exists
- Verify tokens in `config/tokens.json`
- Check DexScreener API availability

### Telegram not working?
- Verify bot token format: `123456789:ABCdefGHIjklMNOpqrSTUvwxyz`
- Get chat ID from @userinfobot
- Check secrets are set correctly

## Workflow File

Location: `.github/workflows/tracker.yml`

Key features:
- Caches pip dependencies
- Caches API responses
- Artifacts retention (7 days)
- Automatic retry on failure
- Summary in commit message

## Manual Run

Go to Actions → "Weirdo Tracker" → "Run workflow" → Enter reason → "Run workflow"

## Next Steps

1. ✅ Push code to GitHub
2. ⬜ Configure Telegram secrets (optional)
3. ⬜ Test manual run
4. ⬜ Verify 15-min schedule works
5. ⬜ Deploy dashboard to Surge.sh
