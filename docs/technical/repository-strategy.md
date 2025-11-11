# RedditHarbor Repository Structure Strategy

**Decision:** Polyrepo (Separate Repositories) with Database as Contract

**Last Updated:** 2025-11-11

---

## TL;DR: The Recommendation

```
Repository Structure: POLYREPO (2 separate repos)

Repo 1: redditharbor (existing Python)
├── GitHub: github.com/ai-rio/redditharbor
├── Hosts: Python scripts, data collection, scoring
├── Deploys: GitHub Actions (cron jobs)
├── Writes: To Supabase database

Repo 2: redditharbor-web (new Next.js)
├── GitHub: github.com/ai-rio/redditharbor-web
├── Hosts: Next.js frontend + API routes
├── Deploys: Vercel (continuous deployment)
├── Reads: From Supabase database

Contract: Supabase database schema (single source of truth)
```

**Why:** Clean separation, independent deployment, minimal coupling, easier to maintain.

---

## Analysis of All Options

### Option 1: Monorepo (Single Repository)

```
redditharbor/
├── .git/
├── python/
│   ├── scripts/
│   ├── core/
│   ├── config/
│   ├── requirements.txt
│   └── pyproject.toml
├── web/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── package.json
│   └── next.config.js
├── docs/
├── .github/
│   └── workflows/
│       ├── python-cron.yml
│       └── web-deploy.yml
└── README.md
```

**Pros:**
- ✅ Single source of truth
- ✅ Easier to keep documentation in sync
- ✅ Single version control history
- ✅ Share types/schemas easily
- ✅ One `git clone` for everything

**Cons:**
- ❌ Larger repo size (slower clones)
- ❌ CI/CD more complex (need to detect which part changed)
- ❌ Deployment still separate anyway (Vercel vs GitHub Actions)
- ❌ Mixed tech stacks in one repo (confusing)
- ❌ Python team sees Next.js changes (noise)
- ❌ Need monorepo tools (Nx, Turborepo, Lerna)

**When to Use:**
- Services share significant code
- Frequent coordinated changes across both
- Single team managing everything
- Need atomic commits across services

**Verdict for RedditHarbor:** ❌ **Not recommended**
- Python and Next.js don't share code
- They communicate via database, not imports
- Independent deployment cycles
- Overkill for your architecture

---

### Option 2: Polyrepo (Separate Repositories) ⭐ RECOMMENDED

```
Repository 1: redditharbor (Python)
github.com/ai-rio/redditharbor/
├── .git/
├── scripts/
├── core/
├── config/
├── docs/
├── tests/
├── .github/workflows/
└── README.md

Repository 2: redditharbor-web (Next.js)
github.com/ai-rio/redditharbor-web/
├── .git/
├── app/
├── components/
├── lib/
├── public/
├── docs/
└── README.md

Contract: Supabase database schema
├── Defined in Supabase migrations
├── Both repos reference same tables
├── Schema docs shared via documentation
```

**Pros:**
- ✅ Clean separation of concerns
- ✅ Independent deployment cycles
- ✅ Smaller, focused repositories
- ✅ No need for monorepo tooling
- ✅ Easier to understand (one responsibility per repo)
- ✅ Can have different contributors per repo
- ✅ Vercel auto-deploys web only
- ✅ GitHub Actions only runs Python when Python changes

**Cons:**
- ❌ Need to keep database schema in sync manually
- ❌ Documentation can diverge
- ❌ Two repos to manage (2x git operations)
- ❌ Shared types need to be duplicated or generated

**How to Mitigate Cons:**
1. **Schema sync:** Use Supabase as single source of truth
2. **Type generation:** Generate TypeScript types from Supabase
3. **Documentation:** Link between repos in README
4. **Shared changes:** Rare, coordinate via issues/PRs

**When to Use:**
- Services communicate via API/database (✅ Your case)
- Different tech stacks (✅ Python vs TypeScript)
- Independent deployment (✅ GitHub Actions vs Vercel)
- Different update frequencies (✅ Daily cron vs iterative)

**Verdict for RedditHarbor:** ✅ **RECOMMENDED**
- Perfect fit for your architecture
- Simplest to maintain
- Standard industry practice for this pattern

---

### Option 3: Service-Based Repos (Microservices)

```
Repo 1: redditharbor-collector
├── Reddit collection scripts
└── Deploy: GitHub Actions

Repo 2: redditharbor-scorer
├── Opportunity scoring logic
└── Deploy: GitHub Actions

Repo 3: redditharbor-api
├── Next.js API routes only
└── Deploy: Vercel

Repo 4: redditharbor-frontend
├── Next.js UI components only
└── Deploy: Vercel

Contract: API specifications between services
```

**Pros:**
- ✅ Maximum separation
- ✅ Each service independently scalable
- ✅ Different teams per service

**Cons:**
- ❌ Massive overkill for your use case
- ❌ 4+ repos to manage
- ❌ Complex coordination
- ❌ Over-engineering for a solo founder/small team

**When to Use:**
- Large teams (10+ engineers)
- True microservices architecture
- Each service is massive
- Need independent scaling per service

**Verdict for RedditHarbor:** ❌ **Overkill**
- You're not Netflix
- Solo founder/small team
- Adds complexity with no benefit

---

### Option 4: Hybrid Monorepo

```
Repo 1: redditharbor (monorepo with workspace)
├── packages/
│   ├── shared/          # Shared types, schemas
│   ├── python/          # Python scripts
│   └── web/             # Next.js
├── .github/workflows/
└── package.json         # Workspace root
```

**Pros:**
- ✅ Shared code in one place
- ✅ Single repo for everything
- ✅ Can share types via packages/shared

**Cons:**
- ❌ Need package manager workspaces (pnpm/yarn/npm)
- ❌ Python doesn't use npm (awkward setup)
- ❌ Still deploy separately anyway
- ❌ More complex than needed

**When to Use:**
- Frontend and backend share significant code
- Using same tech stack across services
- Need to import shared packages

**Verdict for RedditHarbor:** ❌ **Unnecessary complexity**
- Python and Node.js don't share code naturally
- Database schema is the contract, not shared packages

---

## Recommended Structure: Polyrepo Details

### Repository 1: redditharbor (Python - EXISTING)

**Location:** `github.com/ai-rio/redditharbor`

**Purpose:** Data collection, scoring, AI profiling

**Structure:**
```
redditharbor/
├── .github/
│   └── workflows/
│       └── daily-collection.yml          # Cron jobs
├── config/
│   ├── settings.py                       # Environment config
│   └── dlt_settings.py                   # DLT config
├── core/
│   ├── collection.py                     # Reddit collection
│   ├── dlt_reddit_source.py              # DLT source
│   ├── activity_validation.py            # Activity scoring
│   └── supabase_client.py                # Supabase writes
├── scripts/
│   ├── automated_opportunity_collector.py
│   ├── batch_opportunity_scorer.py
│   └── real_ai_app_profiler.py
├── docs/
│   ├── business/                         # Your docs
│   ├── technical/
│   └── guides/
├── tests/
├── pyproject.toml
├── requirements.txt
└── README.md
```

**Deployment:**
- GitHub Actions (cron schedule)
- Runs daily at 9 AM UTC
- Writes to Supabase

**Environment Variables (GitHub Secrets):**
```
SUPABASE_URL
SUPABASE_SERVICE_KEY
REDDIT_CLIENT_ID
REDDIT_CLIENT_SECRET
REDDIT_USER_AGENT
OPENROUTER_API_KEY
```

---

### Repository 2: redditharbor-web (Next.js - NEW)

**Location:** `github.com/ai-rio/redditharbor-web`

**Purpose:** Customer-facing website, dashboard, API routes

**Structure:**
```
redditharbor-web/
├── .github/
│   └── workflows/
│       └── vercel-deploy.yml             # Auto-deploy on push
├── app/
│   ├── page.tsx                          # Landing page
│   ├── pricing/
│   ├── dashboard/
│   ├── opportunities/[id]/
│   ├── auth/
│   └── api/
│       ├── opportunities/
│       ├── user/
│       ├── checkout/
│       └── webhooks/
├── components/
│   ├── ui/                               # Shadcn components
│   ├── OpportunityCard.tsx
│   ├── CredibilityBadge.tsx
│   └── PricingTable.tsx
├── lib/
│   ├── supabase/
│   │   ├── client.ts                     # Client-side
│   │   ├── server.ts                     # Server-side
│   │   └── api.ts                        # API routes
│   ├── stripe.ts
│   └── database.types.ts                 # Generated from Supabase
├── public/
├── docs/
│   └── README.md                         # Link to main repo
├── .env.local.example
├── package.json
├── next.config.js
├── tailwind.config.ts
└── README.md
```

**Deployment:**
- Vercel (auto-deploy on push to main)
- Preview deployments on PRs

**Environment Variables (Vercel):**
```
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
NEXT_PUBLIC_APP_URL
```

---

## The Database Contract

**Supabase is the single source of truth:**

```
Contract between Python and Next.js:

Database Schema (Supabase):
├── opportunities table
├── problem_metrics table
├── workflow_results table
├── users table (Supabase Auth)
└── subscriptions table

Python:  WRITES → Supabase
Next.js: READS  ← Supabase
```

**How to Keep in Sync:**

1. **Use Supabase Migrations as Source of Truth:**
   ```sql
   -- redditharbor/supabase/migrations/xxx_opportunities.sql
   CREATE TABLE opportunities (
     id UUID PRIMARY KEY,
     title TEXT,
     score NUMERIC,
     ...
   );
   ```

2. **Generate Types for Next.js:**
   ```bash
   # In redditharbor-web/
   supabase gen types typescript --linked > lib/database.types.ts
   ```

3. **Python Uses Same Schema:**
   ```python
   # In redditharbor/
   supabase.table('opportunities').insert({
     'title': title,
     'score': score,
     ...
   })
   ```

4. **Documentation Links:**
   ```markdown
   # redditharbor/README.md
   Related repositories:
   - Web frontend: github.com/ai-rio/redditharbor-web

   # redditharbor-web/README.md
   Related repositories:
   - Python backend: github.com/ai-rio/redditharbor
   ```

---

## Deployment Strategy

### Python Repository (redditharbor)

**Hosting:** GitHub Actions (free)

**Workflow:**
```yaml
# .github/workflows/daily-collection.yml
name: Daily Collection
on:
  schedule:
    - cron: '0 9 * * *'  # 9 AM UTC daily
  workflow_dispatch:

jobs:
  collect:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
      - run: pip install -r requirements.txt
      - run: python scripts/automated_opportunity_collector.py
      - run: python scripts/batch_opportunity_scorer.py
      - run: python scripts/real_ai_app_profiler.py
```

**When it runs:**
- Automatically at 9 AM UTC daily
- Manually via "Run workflow" button
- Never "deployed" in traditional sense (just scheduled jobs)

---

### Next.js Repository (redditharbor-web)

**Hosting:** Vercel (free tier)

**Deployment:**
- Push to `main` → Auto-deploys to production
- Push to other branch → Preview deployment
- No workflow needed (Vercel handles it)

**Setup:**
1. Connect GitHub repo to Vercel
2. Configure environment variables
3. Done - auto-deploys forever

---

## Development Workflow

### Working on Python

```bash
# Clone Python repo
git clone github.com/ai-rio/redditharbor
cd redditharbor

# Make changes
vim scripts/automated_opportunity_collector.py

# Test locally
python scripts/automated_opportunity_collector.py

# Commit and push
git add .
git commit -m "feat: improve collection logic"
git push

# GitHub Actions will run on next scheduled time
```

### Working on Next.js

```bash
# Clone Next.js repo
git clone github.com/ai-rio/redditharbor-web
cd redditharbor-web

# Install dependencies
npm install

# Run locally
npm run dev  # http://localhost:3000

# Make changes
vim app/page.tsx

# Commit and push
git add .
git commit -m "feat: add landing page"
git push

# Vercel auto-deploys in 2-3 minutes
```

### Working on Both (Schema Change)

**Example: Adding new column to opportunities table**

```bash
# 1. In redditharbor repo (Python)
cd redditharbor

# Create Supabase migration
supabase migration new add_difficulty_score

# Edit migration
vim supabase/migrations/xxx_add_difficulty_score.sql
# ALTER TABLE opportunities ADD COLUMN difficulty_score NUMERIC;

# Apply migration
supabase db push

# Update Python code
vim scripts/batch_opportunity_scorer.py
# Add difficulty_score to insert

# Commit
git add .
git commit -m "feat: add difficulty scoring"
git push

# 2. In redditharbor-web repo (Next.js)
cd ../redditharbor-web

# Regenerate types
supabase gen types typescript --linked > lib/database.types.ts

# Update Next.js components
vim components/OpportunityCard.tsx
# Add difficulty badge

# Commit
git add .
git commit -m "feat: show difficulty score"
git push

# Both deployed independently
```

---

## Shared Documentation Strategy

### Option A: Keep Docs in Python Repo (Recommended)

```
redditharbor/
└── docs/
    ├── business/
    ├── technical/
    └── guides/

redditharbor-web/
└── README.md  # Links to main docs
```

**Pros:**
- Single source of truth for docs
- Business docs naturally live with data logic

**Cons:**
- Next.js contributors need to look elsewhere for docs

### Option B: Duplicate Minimal Docs

```
redditharbor/
└── docs/
    └── [All docs]

redditharbor-web/
└── docs/
    └── frontend-specific.md
```

**Pros:**
- Each repo self-contained

**Cons:**
- Risk of docs diverging

**Recommendation:** Option A (docs in Python repo, link from Next.js)

---

## Schema Versioning Strategy

**Problem:** How to ensure Python and Next.js use compatible schemas?

**Solution: Database Migrations as Contract**

1. **All schema changes in Supabase migrations:**
   ```
   redditharbor/supabase/migrations/
   ├── 001_initial_schema.sql
   ├── 002_add_problem_metrics.sql
   └── 003_add_difficulty_score.sql
   ```

2. **Python and Next.js both reference same Supabase:**
   - Python writes to tables
   - Next.js reads from tables
   - Supabase enforces schema

3. **Breaking changes are rare:**
   - Adding columns: Safe (Python adds, Next.js ignores until updated)
   - Renaming columns: Coordinate (but rare)
   - Deleting columns: Coordinate (but rare)

4. **Version in package.json/pyproject.toml (optional):**
   ```json
   // redditharbor-web/package.json
   "version": "1.0.0"

   # redditharbor/pyproject.toml
   version = "1.0.0"
   ```

---

## Cost Analysis

### Monorepo Costs
- **Time:** +2-4 hours setup (monorepo tooling)
- **Maintenance:** +10% ongoing (more complex)
- **Mental Overhead:** High (which part changed?)

### Polyrepo Costs
- **Time:** 0 hours setup (just create 2nd repo)
- **Maintenance:** Standard (each repo simple)
- **Mental Overhead:** Low (clear separation)

### Verdict: Polyrepo is cheaper in every dimension

---

## Migration Plan (From Current State)

**Current:** You have `redditharbor` Python repo

**Goal:** Add `redditharbor-web` Next.js repo

### Step-by-Step

```bash
# 1. Create new Next.js repo on GitHub
# Go to github.com → New Repository
# Name: redditharbor-web
# Public/Private: Same as Python repo

# 2. Clone and initialize
git clone github.com/ai-rio/redditharbor-web
cd redditharbor-web

# 3. Create Next.js app
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir

# 4. Follow nextjs-setup-guide.md
# (Install dependencies, create components, etc.)

# 5. Link repos in README
echo "## Related Repositories
- Python backend: github.com/ai-rio/redditharbor
- Database: Supabase (shared)
" >> README.md

# 6. Push
git add .
git commit -m "Initial Next.js setup"
git push

# 7. Connect to Vercel
# Go to vercel.com → Import Project → Select redditharbor-web

# Done! Two independent repos, one system.
```

---

## Troubleshooting Common Issues

### Issue: Schema out of sync

**Symptom:** Next.js expects column that doesn't exist

**Solution:**
```bash
# 1. Check Supabase schema in dashboard
# 2. Regenerate types in redditharbor-web
supabase gen types typescript --linked > lib/database.types.ts
```

### Issue: Environment variables not matching

**Symptom:** Python writes to different Supabase than Next.js reads

**Solution:**
```bash
# Verify both use same Supabase URL
echo $SUPABASE_URL  # In Python
cat .env.local | grep SUPABASE_URL  # In Next.js
```

### Issue: Can't find documentation

**Solution:**
```
Add to redditharbor-web/README.md:
📚 Documentation: See github.com/ai-rio/redditharbor/docs
```

---

## Conclusion

**Recommended Structure: Polyrepo (2 Separate Repositories)**

**Reasoning:**
1. ✅ Clean separation (Python vs Next.js)
2. ✅ Independent deployment (GitHub Actions vs Vercel)
3. ✅ Simple to understand
4. ✅ Standard industry practice
5. ✅ No monorepo tooling needed
6. ✅ Minimal coupling via database

**Not Recommended:**
- ❌ Monorepo: Overkill, adds complexity
- ❌ Service-based: Way too many repos
- ❌ Hybrid: Awkward with Python + Node.js

**Next Steps:**
1. Keep `redditharbor` (Python) as-is
2. Create `redditharbor-web` (Next.js) new repo
3. Link repos in README
4. Deploy Python to GitHub Actions (already done)
5. Deploy Next.js to Vercel (new)
6. Supabase is the contract between them

---

**Document Status:** Complete
**Last Updated:** 2025-11-11
**Decision:** APPROVED - Use Polyrepo
