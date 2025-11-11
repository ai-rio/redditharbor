# Deployment Guide for RedditHarbor

**Goal:** Deploy Next.js to Vercel + Python scripts to GitHub Actions

**Time:** 1-2 hours

**Last Updated:** 2025-11-11

---

## Overview

This guide walks through deploying:
1. **Next.js frontend** → Vercel (free tier)
2. **Python background jobs** → GitHub Actions (free tier)
3. **Custom domain** → redditharbor.com (optional)

---

## Part 1: Deploy Next.js to Vercel

### Step 1.1: Push Code to GitHub

```bash
# In your redditharbor-web directory
git init
git add .
git commit -m "Initial Next.js setup"

# Create GitHub repo (if not exists)
# Go to github.com → New Repository → "redditharbor-web"

git remote add origin https://github.com/YOUR_USERNAME/redditharbor-web.git
git branch -M main
git push -u origin main
```

### Step 1.2: Sign Up for Vercel

1. Go to https://vercel.com/signup
2. Sign up with GitHub
3. Authorize Vercel to access your repositories

### Step 1.3: Import Project

1. Click "Add New Project"
2. Select "redditharbor-web" repository
3. **Configure Project:**
   - **Framework Preset:** Next.js (auto-detected)
   - **Root Directory:** `./` (unless your Next.js is in a subdirectory)
   - **Build Command:** `npm run build` (default)
   - **Output Directory:** `.next` (default)

### Step 1.4: Add Environment Variables

In Vercel project settings, add:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
NEXT_PUBLIC_APP_URL=https://your-app.vercel.app
```

**Important:**
- Don't include spaces around `=`
- Copy full values (no truncation)
- Update `NEXT_PUBLIC_APP_URL` after deployment

### Step 1.5: Deploy

1. Click "Deploy"
2. Wait 2-3 minutes for build
3. Your app will be live at: `https://redditharbor-web-xxx.vercel.app`

### Step 1.6: Test Deployment

Visit your Vercel URL and test:
- [ ] Landing page loads
- [ ] Sign up works
- [ ] Dashboard shows opportunities
- [ ] No console errors

---

## Part 2: Configure Custom Domain (Optional)

### Step 2.1: Add Domain in Vercel

1. Go to Vercel project → Settings → Domains
2. Click "Add Domain"
3. Enter: `redditharbor.com` and `www.redditharbor.com`

### Step 2.2: Update DNS Records

In your domain registrar (Namecheap, GoDaddy, etc.):

**For root domain (redditharbor.com):**
```
Type: A
Name: @
Value: 76.76.21.21  (Vercel IP)
```

**For www subdomain:**
```
Type: CNAME
Name: www
Value: cname.vercel-dns.com
```

**Wait 24-48 hours** for DNS propagation.

### Step 2.3: Update Environment Variables

```bash
# In Vercel, update:
NEXT_PUBLIC_APP_URL=https://redditharbor.com
```

Redeploy for changes to take effect.

---

## Part 3: Set Up Stripe Webhooks

### Step 3.1: Get Webhook Endpoint

Your webhook endpoint will be:
```
https://redditharbor.com/api/webhooks/stripe
```

### Step 3.2: Configure in Stripe

1. Go to https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. **Endpoint URL:** `https://redditharbor.com/api/webhooks/stripe`
4. **Events to listen to:**
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
5. Click "Add endpoint"

### Step 3.3: Get Webhook Secret

1. Click on the webhook you just created
2. Click "Reveal" under "Signing secret"
3. Copy the secret (starts with `whsec_`)

### Step 3.4: Update Vercel Environment

1. Go to Vercel → Settings → Environment Variables
2. Update `STRIPE_WEBHOOK_SECRET` with the new value
3. Redeploy

### Step 3.5: Test Webhook

```bash
# Install Stripe CLI
brew install stripe/stripe-brew/stripe

# Login to Stripe
stripe login

# Forward webhooks to local dev (for testing)
stripe listen --forward-to localhost:3000/api/webhooks/stripe

# Trigger test webhook
stripe trigger checkout.session.completed
```

Check Vercel logs to see if webhook was received.

---

## Part 4: Deploy Python Scripts to GitHub Actions

### Step 4.1: Create GitHub Secrets

In your Python repository (redditharbor):
1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add these secrets:

```
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=RedditHarbor/1.0
OPENROUTER_API_KEY=sk-or-v1-...
```

### Step 4.2: Create GitHub Actions Workflow

```bash
# In your redditharbor directory
mkdir -p .github/workflows
```

Create workflow file:

```yaml
# .github/workflows/daily-collection.yml
name: Daily Reddit Collection

on:
  schedule:
    # Run at 9 AM UTC every day
    - cron: '0 9 * * *'
  workflow_dispatch:  # Allow manual trigger

jobs:
  collect-and-score:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dlt.txt
          pip install -e .

      - name: Run collection script
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
          REDDIT_PUBLIC: ${{ secrets.REDDIT_CLIENT_ID }}
          REDDIT_SECRET: ${{ secrets.REDDIT_CLIENT_SECRET }}
          REDDIT_USER_AGENT: ${{ secrets.REDDIT_USER_AGENT }}
        run: |
          python scripts/automated_opportunity_collector.py

      - name: Run scoring script
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
        run: |
          python scripts/batch_opportunity_scorer.py

      - name: Run AI profiling
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
        run: |
          python scripts/real_ai_app_profiler.py --min-score 85

      - name: Send notification on failure
        if: failure()
        run: |
          echo "Collection workflow failed. Check logs."
          # Add email notification here if needed
```

### Step 4.3: Commit and Push

```bash
git add .github/workflows/daily-collection.yml
git commit -m "Add GitHub Actions workflow for daily collection"
git push origin main
```

### Step 4.4: Test Workflow

1. Go to your GitHub repo → Actions tab
2. Click "Daily Reddit Collection" workflow
3. Click "Run workflow" → "Run workflow"
4. Monitor the logs

**First run might fail** if dependencies are missing. Check logs and fix.

### Step 4.5: Verify Data Flow

After workflow completes:
1. Go to Supabase dashboard
2. Check `opportunities` table has new rows
3. Check Next.js dashboard shows new opportunities

---

## Part 5: Monitor & Maintain

### 5.1: Vercel Monitoring

**Check Deployment Status:**
- Go to https://vercel.com/dashboard
- Click your project
- View recent deployments

**View Logs:**
- Click any deployment
- Click "Functions" tab
- View real-time logs

**Set Up Alerts:**
- Settings → Notifications
- Enable "Deployment Failed" notifications

### 5.2: GitHub Actions Monitoring

**View Workflow Runs:**
- Go to repo → Actions tab
- See all recent runs
- Click any run to see detailed logs

**Set Up Notifications:**
- Settings → Notifications → Actions
- Enable "Email notification on workflow failure"

**Common Issues:**
- ❌ **Timeout:** Increase timeout in workflow file
- ❌ **Rate limit:** Reddit API limits, add delays
- ❌ **Missing secrets:** Double-check secret names match

### 5.3: Supabase Monitoring

**Database Size:**
- Supabase Dashboard → Database → Usage
- Free tier: 500 MB
- Upgrade at $25/mo if needed

**Query Performance:**
- Supabase Dashboard → Database → Query Performance
- Add indexes if queries are slow

**API Usage:**
- Supabase Dashboard → Project Settings → Usage
- Free tier: 2 GB bandwidth/month

---

## Part 6: Continuous Deployment

### 6.1: Auto-Deploy on Push (Vercel)

**Already enabled by default:**
- Push to `main` → Auto-deploys to production
- Push to other branches → Preview deployments

**Preview Deployments:**
```bash
git checkout -b feature/new-page
# Make changes
git commit -m "Add new page"
git push origin feature/new-page

# Vercel creates preview URL
# Test at: https://redditharbor-web-xxx-feature-new-page.vercel.app
```

### 6.2: Staging Environment (Optional)

**Create staging environment:**
1. Create `staging` branch:
   ```bash
   git checkout -b staging
   git push origin staging
   ```

2. In Vercel:
   - Settings → Git
   - Production Branch: `main`
   - Add staging branch → Configure separate domain

3. Use for testing before production:
   ```bash
   git checkout staging
   git merge feature/new-page
   git push origin staging  # Deploys to staging

   # Test on staging.redditharbor.com

   git checkout main
   git merge staging
   git push origin main  # Deploys to production
   ```

---

## Part 7: Rollback Strategy

### 7.1: Rollback Vercel Deployment

If production breaks:
1. Go to Vercel → Deployments
2. Find last working deployment
3. Click ⋯ → "Promote to Production"
4. Instantly reverts to previous version

### 7.2: Rollback GitHub Actions

If collection script breaks:
1. Go to Actions → Daily Reddit Collection
2. Disable workflow temporarily
3. Fix code locally
4. Push fix
5. Re-enable workflow

### 7.3: Rollback Database Changes

**If bad data was inserted:**
```sql
-- Delete data from specific time range
DELETE FROM opportunities
WHERE created_at >= '2025-11-11 09:00:00';

-- Or restore from Supabase backup
-- Supabase Dashboard → Database → Backups
```

---

## Part 8: Performance Optimization

### 8.1: Next.js Optimizations

**Enable Edge Runtime for API Routes:**
```typescript
// app/api/opportunities/route.ts
export const runtime = 'edge'  // Runs on Vercel Edge Network
```

**Add Caching:**
```typescript
// app/dashboard/page.tsx
export const revalidate = 300  // Revalidate every 5 minutes
```

**Optimize Images:**
```typescript
import Image from 'next/image'

<Image
  src="/logo.png"
  width={200}
  height={200}
  alt="Logo"
  priority  // Preload important images
/>
```

### 8.2: Supabase Optimizations

**Add Indexes:**
```sql
-- Speed up common queries
CREATE INDEX idx_opportunities_score ON opportunities(score DESC);
CREATE INDEX idx_opportunities_created_at ON opportunities(created_at DESC);
CREATE INDEX idx_opportunities_subreddit ON opportunities(subreddit);
```

**Use Connection Pooling:**
```typescript
// lib/supabase/server.ts
export function createClient() {
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      db: {
        schema: 'public',
      },
      global: {
        headers: { 'x-supabase-connection-pool': 'true' },
      },
    }
  )
}
```

### 8.3: GitHub Actions Optimizations

**Cache Python Dependencies:**
```yaml
- name: Cache Python dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

**Run Jobs in Parallel:**
```yaml
jobs:
  collect:
    runs-on: ubuntu-latest
    steps:
      - run: python scripts/automated_opportunity_collector.py

  score:
    runs-on: ubuntu-latest
    needs: collect  # Wait for collect to finish
    steps:
      - run: python scripts/batch_opportunity_scorer.py
```

---

## Part 9: Cost Breakdown

### Current Setup (Free Tier)

| Service | Free Tier | Monthly Cost |
|---------|-----------|--------------|
| Vercel | 100 GB bandwidth | $0 |
| Supabase | 500 MB database, 2 GB bandwidth | $0 |
| GitHub Actions | 2,000 minutes | $0 |
| **Total** | | **$0** |

### When to Upgrade

**Vercel Pro ($20/mo):**
- Upgrade when: 10,000+ users or 100 GB+ bandwidth
- Benefits: Better performance, team features

**Supabase Pro ($25/mo):**
- Upgrade when: 50,000+ opportunities or slow queries
- Benefits: 8 GB database, 50 GB bandwidth, better performance

**GitHub Actions (Paid):**
- Upgrade when: Running 10+ workflows per day
- Cost: $0.008/minute after free tier

### Expected Timeline

- **Months 0-3:** Free tier ($0/mo)
- **Months 3-6:** Supabase Pro ($25/mo)
- **Months 6-12:** Add Vercel Pro ($45/mo total)
- **Year 2+:** Custom hosting as needed

---

## Part 10: Troubleshooting

### Issue: Vercel Build Fails

**Error:** "Module not found"
**Solution:**
```bash
# Make sure all dependencies are in package.json
npm install <missing-package>
git commit -am "Add missing dependency"
git push
```

**Error:** "Environment variable not set"
**Solution:**
- Check Vercel → Settings → Environment Variables
- Make sure names match exactly
- Redeploy after adding variables

### Issue: GitHub Actions Fails

**Error:** "Permission denied"
**Solution:**
- Check GitHub secrets are named correctly
- Verify Supabase service key has write permissions

**Error:** "Rate limited by Reddit"
**Solution:**
- Add delays between Reddit API calls
- Reduce number of subreddits collected per run

**Error:** "Timeout after 6 hours"
**Solution:**
```yaml
# Increase timeout in workflow
jobs:
  collect:
    timeout-minutes: 360  # 6 hours (max)
```

### Issue: Data Not Showing in Next.js

**Possible causes:**
1. **RLS blocking access:** Disable temporarily for testing
2. **Workflow didn't run:** Check Actions tab
3. **Wrong table name:** Verify table names match

---

## Part 11: Security Checklist

Before going live:
- [ ] All secrets are in environment variables (not hardcoded)
- [ ] Supabase RLS policies enabled
- [ ] Stripe webhook signature verification enabled
- [ ] HTTPS everywhere (Vercel handles this)
- [ ] Rate limiting on API routes
- [ ] CORS configured properly
- [ ] No sensitive data in client-side code
- [ ] GitHub secrets configured properly

---

## Part 12: Launch Checklist

Final checks before announcing:
- [ ] Custom domain working (if using)
- [ ] All pages load without errors
- [ ] Sign up/sign in flow works
- [ ] Dashboard shows opportunities
- [ ] Stripe payments work (test mode)
- [ ] Python cron jobs running daily
- [ ] Email alerts working
- [ ] Mobile responsive
- [ ] SEO meta tags added
- [ ] Analytics set up (PostHog/Google Analytics)

---

## Next Steps

1. **Test thoroughly** - Use staging environment
2. **Switch Stripe to live mode** - When ready for real customers
3. **Monitor for 1 week** - Make sure cron jobs run successfully
4. **Launch!** - Follow `docs/business/launch-checklist.md`

---

## Resources

- **Vercel Docs:** https://vercel.com/docs
- **GitHub Actions Docs:** https://docs.github.com/en/actions
- **Supabase Docs:** https://supabase.com/docs
- **Stripe Webhooks:** https://stripe.com/docs/webhooks

---

**Document Status:** Complete
**Last Updated:** 2025-11-11
**Next:** Read `api-examples.md` for API route code examples
