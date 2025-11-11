# RedditHarbor Technical Architecture

**Architecture Type:** Next.js Frontend + Supabase Direct + Python Background Jobs
**Last Updated:** 2025-11-11
**Status:** Approved for Implementation

---

## Overview

RedditHarbor uses a **hybrid architecture** that combines:
- **Next.js** for frontend and API routes (customer-facing)
- **Supabase** as the single source of truth (database + auth + storage)
- **Python** for data collection and processing (background jobs)

This architecture allows us to **launch in 7-14 days** by reusing 100% of existing Python code while building a modern web frontend.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USERS (Browsers)                            │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      Next.js Application                             │
│                      (Vercel - Free Tier)                            │
│                                                                       │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  Pages/Routes   │  │   API Routes     │  │  Stripe Webhook  │  │
│  │  - Landing      │  │  - /opportunities│  │  - /webhooks     │  │
│  │  - Dashboard    │  │  - /auth         │  │                   │  │
│  │  - Pricing      │  │  - /user         │  │                   │  │
│  └─────────────────┘  └──────────────────┘  └──────────────────┘  │
│                            │                                          │
└────────────────────────────┼─────────────────────────────────────────┘
                             │
                             ↓ (Direct PostgreSQL queries)
┌─────────────────────────────────────────────────────────────────────┐
│                      Supabase Database                               │
│                      (PostgreSQL + Auth + Storage)                   │
│                                                                       │
│  Tables:                                                              │
│  - opportunities (your scored app ideas)                             │
│  - problem_metrics (credibility data)                                │
│  - workflow_results (AI profiles)                                    │
│  - users (Supabase Auth)                                             │
│  - subscriptions (Stripe customer data)                              │
│                                                                       │
└────────────────────────────┬────────────────────────────────────────┘
                             ↑ (Writes data)
                             │
┌────────────────────────────┴────────────────────────────────────────┐
│                    Python Background Jobs                            │
│                    (GitHub Actions Cron / Railway)                   │
│                                                                       │
│  Daily Jobs (9 AM):                                                  │
│  1. automated_opportunity_collector.py → Collect from Reddit         │
│  2. batch_opportunity_scorer.py → Score opportunities                │
│  3. real_ai_app_profiler.py → AI profiling (top opportunities)      │
│                                                                       │
│  All write to → Supabase                                             │
└─────────────────────────────────────────────────────────────────────┘

External Services:
- Stripe (payments)
- Resend/SendGrid (email alerts)
- OpenRouter (AI profiling - already integrated)
```

---

## Component Details

### 1. Next.js Application (Frontend + API)

**Technology:** Next.js 14 (App Router), TypeScript, Tailwind CSS

**Responsibilities:**
- Serve customer-facing website (landing, pricing, dashboard)
- User authentication (via Supabase Auth)
- Read opportunities from Supabase
- Handle Stripe payments
- Send email alerts to users

**Hosting:** Vercel (Free tier supports thousands of users)

**Key Files:**
```
redditharbor-web/
├── app/
│   ├── page.tsx                    # Landing page
│   ├── dashboard/
│   │   └── page.tsx                # User dashboard
│   ├── pricing/
│   │   └── page.tsx                # Pricing page
│   ├── opportunities/
│   │   └── [id]/page.tsx           # Opportunity detail
│   └── api/
│       ├── opportunities/
│       │   └── route.ts            # GET /api/opportunities
│       ├── user/
│       │   └── route.ts            # GET /api/user
│       └── webhooks/
│           └── stripe/route.ts     # POST /api/webhooks/stripe
├── components/
│   ├── OpportunityCard.tsx
│   ├── CredibilityBadge.tsx
│   └── PricingTable.tsx
└── lib/
    ├── supabase.ts                 # Supabase client
    └── stripe.ts                   # Stripe client
```

---

### 2. Supabase (Database + Auth + Storage)

**Technology:** PostgreSQL 15, Supabase Auth, Supabase Storage

**Responsibilities:**
- Store all opportunity data
- User authentication and authorization
- Row-level security (RLS) policies
- Real-time subscriptions (optional for future)

**Tables We Use:**

#### `opportunities` (Your existing table)
```sql
- id (uuid)
- opportunity_id (varchar) - Reddit post ID
- title (text)
- description (text)
- score (numeric) - 0-100 AI score
- subreddit (varchar)
- comment_count (integer)
- created_at (timestamp)
```

#### `problem_metrics` (Credibility layer)
```sql
- id (uuid)
- opportunity_id (uuid) - FK to opportunities
- comment_count (integer)
- trending_score (numeric)
- subreddit_spread (integer)
- intent_signals (integer)
- credibility_score (numeric)
```

#### `workflow_results` (AI profiles)
```sql
- id (uuid)
- opportunity_id (varchar)
- app_name (varchar)
- problem_statement (text)
- target_users (text)
- core_functions (jsonb)
- monetization_model (text)
```

#### `users` (Supabase Auth - managed)
```sql
- id (uuid)
- email (varchar)
- created_at (timestamp)
- subscription_tier (varchar) - free/starter/pro/agency
```

#### `subscriptions` (Custom table)
```sql
- id (uuid)
- user_id (uuid) - FK to users
- stripe_customer_id (varchar)
- stripe_subscription_id (varchar)
- tier (varchar) - starter/pro/agency
- status (varchar) - active/canceled/past_due
- current_period_end (timestamp)
```

**Row-Level Security (RLS):**
```sql
-- Users can only see their own opportunities (based on tier limits)
CREATE POLICY "Users can view opportunities based on tier"
ON opportunities FOR SELECT
USING (
  -- Free tier: 5/month, Starter: 20/month, Pro: 100/month, Agency: unlimited
  CASE
    WHEN auth.jwt()->>'subscription_tier' = 'agency' THEN true
    WHEN auth.jwt()->>'subscription_tier' = 'pro'
      THEN id IN (
        SELECT id FROM opportunities
        WHERE created_at >= date_trunc('month', CURRENT_DATE)
        ORDER BY score DESC
        LIMIT 100
      )
    WHEN auth.jwt()->>'subscription_tier' = 'starter'
      THEN id IN (
        SELECT id FROM opportunities
        WHERE created_at >= date_trunc('month', CURRENT_DATE)
        ORDER BY score DESC
        LIMIT 20
      )
    ELSE id IN (
      SELECT id FROM opportunities
      WHERE created_at >= date_trunc('month', CURRENT_DATE)
      ORDER BY score DESC
      LIMIT 5
    )
  END
);
```

---

### 3. Python Background Jobs (Data Pipeline)

**Technology:** Python 3.12, PRAW, DLT, existing codebase

**Responsibilities:**
- Collect Reddit data (your existing scripts)
- Score opportunities (your existing scoring logic)
- Run AI profiling (your existing OpenRouter integration)
- Write results to Supabase

**Existing Scripts (No Changes Needed):**
```python
# scripts/automated_opportunity_collector.py
# - Collects from Reddit using DLT
# - Writes to Supabase opportunities table
# - Already working ✅

# scripts/batch_opportunity_scorer.py
# - Scores opportunities with 5-factor framework
# - Updates score column in opportunities table
# - Already working ✅

# scripts/real_ai_app_profiler.py
# - Uses OpenRouter + Claude for AI profiling
# - Writes to workflow_results table
# - Already working ✅
```

**Cron Schedule:**
```yaml
# .github/workflows/daily-collection.yml
name: Daily Reddit Collection
on:
  schedule:
    - cron: '0 9 * * *'  # 9 AM UTC daily
  workflow_dispatch:      # Manual trigger

jobs:
  collect:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: python scripts/automated_opportunity_collector.py
      - run: python scripts/batch_opportunity_scorer.py
      - run: python scripts/real_ai_app_profiler.py --min-score 85
    env:
      SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
      SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
      REDDIT_CLIENT_ID: ${{ secrets.REDDIT_CLIENT_ID }}
      REDDIT_CLIENT_SECRET: ${{ secrets.REDDIT_CLIENT_SECRET }}
      OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
```

**Execution Flow:**
1. **9:00 AM UTC:** GitHub Actions triggers workflow
2. **9:00-9:20 AM:** Collection script runs (6,000+ submissions)
3. **9:20-9:40 AM:** Scoring script runs (score all opportunities)
4. **9:40-10:00 AM:** AI profiling runs (top 50 opportunities with score 85+)
5. **10:00 AM:** All data in Supabase, visible to Next.js users immediately

---

## Data Flow

### User Viewing Opportunities (Read Path)

```
User Browser
    ↓
Next.js Page (/dashboard)
    ↓
Next.js API Route (/api/opportunities)
    ↓
Supabase Client (with user JWT)
    ↓
PostgreSQL Query (with RLS filtering)
    ↓
Returns opportunities[] to Next.js
    ↓
Rendered in React components
    ↓
Displayed to user
```

**Code Example:**
```typescript
// app/api/opportunities/route.ts
export async function GET(request: Request) {
  const supabase = createServerClient() // Uses user's JWT

  const { data: opportunities, error } = await supabase
    .from('opportunities')
    .select(`
      *,
      problem_metrics(*),
      workflow_results(*)
    `)
    .gte('score', 70)
    .order('score', { ascending: false })

  return Response.json(opportunities)
}
```

### Python Collecting Data (Write Path)

```
GitHub Actions Cron (9 AM)
    ↓
Python Script Starts
    ↓
PRAW → Reddit API (collect submissions/comments)
    ↓
DLT Pipeline (validate, transform)
    ↓
Supabase Client (service key)
    ↓
PostgreSQL INSERT (opportunities, problem_metrics)
    ↓
Data immediately available to Next.js
```

**Code Example (Existing - No Changes):**
```python
# Your existing code in automated_opportunity_collector.py
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# This already works!
supabase.table('opportunities').insert({
    'opportunity_id': submission.id,
    'title': submission.title,
    'score': calculated_score,
    'subreddit': submission.subreddit.display_name,
    # ... etc
}).execute()
```

---

## Authentication Flow

**Using Supabase Auth (Built-in):**

```
1. User clicks "Sign Up"
    ↓
2. Next.js calls Supabase Auth
    ↓
3. Supabase creates user + sends verification email
    ↓
4. User clicks email link
    ↓
5. Supabase sets session cookie
    ↓
6. Next.js reads session from cookie
    ↓
7. User can now access dashboard
```

**Code Example:**
```typescript
// app/auth/signup/page.tsx
'use client'

import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'

export default function SignUp() {
  const supabase = createClientComponentClient()

  async function handleSignUp(email: string, password: string) {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: `${location.origin}/auth/callback`
      }
    })
  }

  // ... form UI
}
```

---

## Payment Flow (Stripe)

```
1. User clicks "Upgrade to Pro"
    ↓
2. Next.js creates Stripe Checkout session
    ↓
3. User redirected to Stripe hosted page
    ↓
4. User enters payment info
    ↓
5. Stripe processes payment
    ↓
6. Stripe sends webhook to /api/webhooks/stripe
    ↓
7. Next.js updates subscriptions table
    ↓
8. User's tier updated in Supabase Auth metadata
    ↓
9. RLS policies grant access to more opportunities
```

**Code Example:**
```typescript
// app/api/checkout/route.ts
import Stripe from 'stripe'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

export async function POST(request: Request) {
  const { priceId, userId } = await request.json()

  const session = await stripe.checkout.sessions.create({
    customer: userId,
    line_items: [{ price: priceId, quantity: 1 }],
    mode: 'subscription',
    success_url: `${origin}/dashboard?success=true`,
    cancel_url: `${origin}/pricing?canceled=true`,
  })

  return Response.json({ url: session.url })
}
```

```typescript
// app/api/webhooks/stripe/route.ts
export async function POST(request: Request) {
  const body = await request.text()
  const sig = request.headers.get('stripe-signature')!

  const event = stripe.webhooks.constructEvent(body, sig, webhookSecret)

  if (event.type === 'checkout.session.completed') {
    const session = event.data.object

    // Update user's subscription tier in Supabase
    await supabase
      .from('subscriptions')
      .insert({
        user_id: session.metadata.userId,
        stripe_customer_id: session.customer,
        stripe_subscription_id: session.subscription,
        tier: session.metadata.tier,
        status: 'active'
      })

    // Update user metadata for RLS
    await supabase.auth.admin.updateUserById(
      session.metadata.userId,
      { user_metadata: { subscription_tier: session.metadata.tier } }
    )
  }

  return Response.json({ received: true })
}
```

---

## Email Alerts Flow

```
1. Python scoring completes (finds 60+ score opportunity)
    ↓
2. Python writes to opportunities table
    ↓
3. Python triggers Next.js API route: POST /api/alerts/trigger
    ↓
4. Next.js queries users with email_alerts = true
    ↓
5. Next.js sends emails via Resend/SendGrid
    ↓
6. Users receive "New High-Score Opportunity" email
```

**Alternative (Simpler):**
```
1. Python scoring completes
    ↓
2. Python directly sends emails via SMTP
    ↓
3. No Next.js involved (your existing code can do this)
```

---

## Deployment Architecture

### Next.js (Vercel)
- **Auto-deploy:** Push to main branch → auto deploy
- **Environment variables:** SUPABASE_URL, SUPABASE_ANON_KEY, STRIPE_SECRET_KEY
- **Custom domain:** redditharbor.com (configure in Vercel)
- **Edge runtime:** API routes run on Vercel Edge (fast globally)

### Python Jobs (GitHub Actions)
- **Free:** 2,000 minutes/month on free tier (plenty for daily jobs)
- **Secrets:** Configure in repo Settings → Secrets
- **Monitoring:** View workflow runs in Actions tab
- **Manual trigger:** Can run workflows on-demand

### Supabase
- **Free tier:** 500 MB database, 2 GB bandwidth, 50k monthly active users
- **Upgrade if needed:** $25/mo for Pro (8 GB database, 50 GB bandwidth)
- **Backups:** Daily automated backups included
- **Monitoring:** Dashboard shows query performance, storage usage

---

## Scalability Considerations

### Current Limits (Free Tier)

| Component | Free Tier Limit | When to Upgrade |
|-----------|----------------|-----------------|
| Vercel | 100 GB bandwidth/mo | 10,000+ users |
| Supabase | 500 MB database | 50,000+ opportunities |
| GitHub Actions | 2,000 minutes/mo | 10+ jobs/day |

### Growth Path

**0-100 customers:** Free tier works perfectly
**100-500 customers:** Upgrade Supabase to Pro ($25/mo)
**500-2,000 customers:** Add Vercel Pro ($20/mo) for better performance
**2,000+ customers:** Consider managed Python hosting (Railway $20/mo)

---

## Security Considerations

### Authentication
- ✅ Supabase Auth handles passwords (bcrypt hashing)
- ✅ JWT tokens with 1-hour expiry
- ✅ Refresh tokens stored in httpOnly cookies
- ✅ Email verification required

### Authorization
- ✅ Row-Level Security (RLS) on all tables
- ✅ Users can only access opportunities allowed by tier
- ✅ API routes verify user session before queries
- ✅ Service keys only in server-side code/Python scripts

### Payments
- ✅ Stripe handles all payment data (PCI compliant)
- ✅ Never store credit cards
- ✅ Webhook signature verification
- ✅ Idempotency keys prevent duplicate charges

### Data Privacy
- ✅ Reddit data is public (no PII concerns)
- ✅ User emails encrypted at rest (Supabase)
- ✅ HTTPS everywhere (Vercel + Supabase)
- ✅ GDPR-compliant data deletion on request

---

## Monitoring & Observability

### Next.js (Vercel)
- **Built-in analytics:** Page views, response times, errors
- **Logs:** Real-time logs in Vercel dashboard
- **Errors:** Automatic error detection and notifications

### Python Jobs (GitHub Actions)
- **Workflow runs:** View status, logs, timing
- **Notifications:** Email on workflow failure
- **Manual re-run:** One-click retry on failures

### Supabase
- **Query performance:** Slow query detection
- **Database size:** Storage usage monitoring
- **API usage:** Request count, bandwidth

### Optional: Add Later
- **Sentry:** Error tracking for Next.js ($0-26/mo)
- **PostHog:** Product analytics ($0-450/mo)
- **Better Uptime:** Uptime monitoring ($0-10/mo)

---

## Development Workflow

### Local Development

```bash
# Terminal 1: Next.js frontend
cd redditharbor-web
npm run dev  # http://localhost:3000

# Terminal 2: Python scripts (when testing)
cd redditharbor
python scripts/automated_opportunity_collector.py
```

**Environment Variables (.env.local):**
```bash
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxx...
SUPABASE_SERVICE_KEY=eyJxxx...  # Server-side only
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
```

### Testing Flow

1. **Test Python scripts locally:** Writes to Supabase
2. **Test Next.js locally:** Reads from Supabase (sees data from step 1)
3. **Test payments:** Use Stripe test mode cards
4. **Test email alerts:** Use Resend test mode

### Deployment Flow

```bash
# Next.js deployment (automatic)
git add .
git commit -m "feat: add opportunity dashboard"
git push origin main  # Auto-deploys to Vercel

# Python jobs (automatic via cron)
# Just push code to main, GitHub Actions picks it up
```

---

## Migration Path (Current → New Architecture)

### Phase 1: Next.js Setup (Week 1)
- [ ] Create Next.js app
- [ ] Connect to existing Supabase
- [ ] Build landing page
- [ ] Build dashboard (read opportunities)
- [ ] Deploy to Vercel

### Phase 2: Auth & Payments (Week 2)
- [ ] Add Supabase Auth
- [ ] Add Stripe integration
- [ ] Add pricing tiers
- [ ] Test payment flow end-to-end

### Phase 3: Python Integration (Week 2)
- [ ] Set up GitHub Actions cron
- [ ] Test Python scripts run on schedule
- [ ] Verify data flows to Supabase → Next.js

### Phase 4: Launch (Week 2-3)
- [ ] Custom domain setup
- [ ] Email alerts
- [ ] Analytics setup
- [ ] Launch! 🚀

**Total Time:** 2-3 weeks from start to launch

---

## Alternatives Considered

### Why Not FastAPI Backend?
- **Overkill for MVP:** Python scripts don't need real-time API
- **Extra complexity:** Another service to deploy and manage
- **Extra cost:** $5-20/mo for hosting
- **Can add later:** If we need real-time features, easy to add

### Why Not Convex?
- **Massive rewrite:** All Python code → TypeScript
- **Database migration:** Supabase → Convex schema
- **3-6 months work:** Not compatible with "launch in 30 days"
- **No clear benefit:** Supabase + Next.js already provides everything needed

### Why Not Build Custom Backend?
- **Time:** 3+ months to build properly
- **Maintenance:** Need to manage servers, databases, auth, payments
- **Cost:** $50-200/mo for hosting
- **Risk:** More complexity = more failure points

**Conclusion:** Next.js + Supabase Direct is the right architecture for speed-to-market while preserving all Python code.

---

## Next Steps

1. **Read:** `docs/technical/nextjs-setup-guide.md` for step-by-step Next.js setup
2. **Read:** `docs/technical/deployment-guide.md` for Vercel + GitHub Actions setup
3. **Read:** `docs/technical/api-examples.md` for code examples

**Questions?** Review this doc with your team or ask for clarification on any section.

---

**Document Owner:** Technical Team
**Last Updated:** 2025-11-11
**Status:** Ready for Implementation
