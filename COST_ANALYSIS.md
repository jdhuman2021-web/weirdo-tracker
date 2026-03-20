# Cost Analysis - Weirdo Tracker GitHub Actions

## Current Plan: 30-Minute Intervals

### GitHub Actions Free Tier
- **Limit:** 2,000 minutes/month
- **Price if exceeded:** $0.008/minute

### Usage Calculation

| Interval | Runs/Day | Runs/Month | Est. Minutes | Cost |
|----------|----------|------------|--------------|------|
| 15 min | 96 | ~2,880 | ~5,760 min | **$30/month** |
| 20 min | 72 | ~2,160 | ~4,320 min | **$18/month** |
| 30 min | 48 | ~1,440 | ~2,880 min | **$7/month** |
| 1 hour | 24 | ~720 | ~1,440 min | **FREE** |

**30-minute interval = ~2,880 min/month → ~$7/month overage**

---

## Cost Reduction Options

### Option 1: Stay at 30 Min, Pay $7/month
**Pros:**
- ✅ Frequent updates
- ✅ Catches moves quickly
- ✅ No infrastructure to manage

**Cons:**
- ❌ Recurring cost
- ❌ Still 40% over free tier

---

### Option 2: Reduce to 1 Hour (FREE)
**Pros:**
- ✅ Completely free
- ✅ 1,440 min/month (under limit)

**Cons:**
- ❌ Less frequent data
- ❌ May miss fast pumps/dumps

**Best for:** Passive monitoring

---

### Option 3: Self-Hosted Runner (FREE)
**Setup:** Run on your own machine

**Pros:**
- ✅ Completely free
- ✅ Can run every 5 min if you want
- ✅ No rate limits
- ✅ Data stays local

**Cons:**
- ❌ Your PC must stay on
- ❌ Requires setup

**Implementation:**
```yaml
runs-on: self-hosted  # Instead of ubuntu-latest
```

**Your PC as runner:**
- Install GitHub Actions runner
- Runs when PC is on
- Free unlimited minutes

---

### Option 4: Hybrid Approach (RECOMMENDED)
**Strategy:**
- GitHub Actions: 1 hour (free backup)
- Local script: Every 5-15 min (when PC is on)

**Pros:**
- ✅ Free GitHub tier
- ✅ Fast local updates
- ✅ Cloud backup
- ✅ Best of both worlds

**Files needed:**
- `local_runner.ps1` - Runs agents locally
- Windows Task Scheduler for automation

---

### Option 5: Alternative Platforms

| Platform | Free Tier | Notes |
|----------|-----------|-------|
| **GitLab CI** | 400 min/month | Less than GitHub |
| **Render** | 750 hours/month | Good for web services |
| **Railway** | $5 credit/month | Pay as you go |
| **Fly.io** | $5 credit/month | Good for containers |
| **Vercel** | Unlimited (serverless) | Good for scheduled functions |

**Vercel Option:**
```javascript
// Serverless function that runs via cron
export default async function handler(req, res) {
  // Fetch and save data
}
```
- Free tier: Unlimited serverless functions
- Cron jobs: Included

---

## Recommendation

### Phase 1: GitHub Actions at 1 Hour (FREE)
- Start free
- See if data quality is sufficient

### Phase 2: Add Local Runner (OPTIONAL)
- Run every 15 min on your PC
- Keep GitHub as backup

### Phase 3: Vercel Migration (FUTURE)
- If you need more frequent updates
- Truly free for this use case

---

## Current Decision

**✅ Changed to 30 minutes** - Committing now.

**Next decision needed:**
1. **Keep 30 min** → Pay ~$7/month
2. **Switch to 1 hour** → Completely free
3. **Set up self-hosted** → Free + frequent updates
4. **Hybrid approach** → Free + best performance

---

## Quick Math: Your Setup

**At 30 minutes:**
- 48 runs/day × 2 min = 96 min/day
- 96 × 30 days = 2,880 min/month
- **Overage:** 880 minutes
- **Cost:** 880 × $0.008 = **$7.04/month**

**At 1 hour:**
- 24 runs/day × 2 min = 48 min/day
- 48 × 30 days = 1,440 min/month
- **Under 2,000 limit**
- **Cost:** $0 (FREE)

---

## My Suggestion

**Go with 1 hour for now.** Reasons:

1. **Completely free**
2. **Sufficient for most meme coins** (they don't move that fast)
3. **Can always increase frequency later**
4. **Keep complexity low**

**If you need faster:** Set up local runner on your PC for 15-min updates.

---

What's your preference?
- A) Keep 30 min, pay $7/month
- B) Switch to 1 hour, free
- C) Set up self-hosted runner
- D) Hybrid (1 hour cloud + 15 min local)
