---
chunk: 10/13
source: Claude Code  Claude.md
tokens: ~3219
---

# Example usage:
text = "We're a team of 12 paying $360/month for Asana. Need alternative by end of Q1."
signals = extract_lead_signals(text)

# Returns:
{
  "budget_mentioned": "$360/month",
  "team_size": "12",
  "current_tool": "Asana",
  "urgency": "high",
  "decision_stage": "active_evaluation"
}
```

**That's it. Simple regex + keyword matching. No AI needed for extraction.**

___

## **Your Unfair Advantages for Option B:**

### **1\. You Have 10+ Years B2B Sales Experience**

-   You know what sales teams need
-   You understand buyer intent
-   You know CRM workflows
-   You can sell to VPs of Sales (your former peers)

**This is MASSIVE.** Most technical founders can't sell. You can.

### **2\. You Hate Corporate**

-   You won't over-engineer
-   You'll build what sells, not what's perfect
-   You'll hustle (corporate refugees always do)
-   You want freedom, not another job

**This motivates you to get to $10k MRR fast, not build forever.**

### **3\. You're Building for Yourself**

-   You're validating by using it yourself first
-   Dogfooding = product-market fit
-   Your pain = their pain

___

## **Validation Strategy (Before Full Pivot):**

### **Week 1-2: Proof of Concept**

**Build:** Simple lead extraction + Slack alerts  
**Test:** Monitor 5 competitor keywords for YOUR target product  
**Validate:** Do you get valuable leads?

**Cost:** 20 hours of work  
**Risk:** Low (just testing)

### **Week 3: Customer Discovery (5-10 calls)**

**Target:** B2B SaaS founders/sales leaders on Twitter/LinkedIn

**Script:**

```
Hey [Name],

Quick question: Do your sales reps ever check Reddit for people 
complaining about your competitors?

I built a tool that monitors Reddit 24/7 and sends Slack alerts when
someone posts:
- "Looking for [Competitor] alternatives"
- Mentions budget/team size
- Shows buying intent

Would a 15-min demo be useful?
```

**Goal:** 3-5 people say "Yes, I'd pay for that"

**Cost:** 10 hours (calls + emails)  
**Risk:** Low (just talking)

### **Week 4: Beta Launch**

**Build:** Basic dashboard + CRM export  
**Price:** $299/month beta (50% off)  
**Target:** 3 paying customers

**Goal:** $900/month ← **Validates Option B**

**Cost:** 40 hours  
**Risk:** Medium (but validates before full pivot)

___

## **My Honest Answer to Your Blind Spot:**

### **You're in a blind spot because:**

1.  **You're thinking too hard:** Lead extraction is SIMPLE (regex + keywords)
2.  **You have the data:** It's already in `app_opportunities_trust`
3.  **You have the scoring:** OpportunityAnalyzerAgent already works
4.  **You're missing one field:** Just keep `author` from Reddit

**You don't need new AI. You need to reframe what you have.**

___

## **The Real Question:**

**"Do I want to build a $5k/month lifestyle business (Option A) or a $100k/month company (Option B)?"**

Given:

-   You hate corporate
-   You have B2B sales skills
-   You want AI/digital freedom
-   You can commit 4 weeks

**My recommendation: Validate Option B first (4 weeks), then decide.**

**If validation fails → Option A is still there**  
**If validation succeeds → 10-100x bigger opportunity**

___

## **Next Step:**

Want me to:

1.  **Build the lead extraction code** (show you EXACTLY how it works)?
2.  **Write the customer discovery script** (help you get 5 calls)?
3.  **Map out the 4-week validation plan** (week-by-week tasks)?

**Which would remove the blind spot fastest for you?**

1

●

Perfect! Let me build the **exact** lead extraction code that works with your existing pipeline.

___

●

Update Todos

└

☐ Building lead extraction module

☐ Create integration with existing pipeline

☐ Add customer\_leads table migration

☐ Create demo script showing real examples

☐ Commit all changes

●

Write/home/user/redditharbor/core/lead\_extractor.py

└

1+

`#!/usr/bin/env python3`

2+

`"""`

3+

`Lead Extraction Engine for Option B (Customer Lead Generation)`

4+

5+

`This module extracts actionable sales leads from Reddit posts.`

6+

`Works with existing RedditHarbor pipeline - just adds lead-specific parsing.`

7+

8+

`Key Insight: We're ALREADY collecting this data. We just need to extract:`

9+

`- Reddit username (the actual lead!)`

10+

`- Budget signals`

11+

`- Competitor mentions`

12+

`- Team size`

13+

`- Urgency indicators`

14+

`- Buying intent signals`

15+

16+

`This is SIMPLE: Regex + keyword matching. No complex AI needed.`

17+

`"""`

18+

19+

`import re`

20+

`from dataclasses import dataclass`

Show full diff (582 more lines)

●

Update Todos

└

☐ Build lead extraction module

☐ Creating integration with existing pipeline

☐ Add customer\_leads table migration

☐ Create demo script showing real examples

☐ Commit all changes

●

Write/home/user/redditharbor/supabase/migrations/20251114110000\_add\_customer\_leads\_table.sql

└

1+

`-- Customer Leads Table for Option B (Lead Generation)`

2+

`-- This table stores Reddit users as sales leads (not app ideas)`

3+

4+

`CREATE TABLE IF NOT EXISTS customer_leads (`

5+

`id uuid PRIMARY KEY DEFAULT gen_random_uuid(),`

6+

7+

`-- Lead Identification (THE ACTUAL LEAD!)`

8+

`reddit_username VARCHAR(255) NOT NULL,`

9+

`reddit_post_id TEXT NOT NULL,`

10+

`reddit_post_url TEXT,`

11+

12+

`-- Problem Context`

13+

`problem_description TEXT NOT NULL,`

14+

`full_text TEXT,`

15+

`current_solution VARCHAR(255), -- "Asana", "MyFitnessPal", etc.`

16+

`competitor_mentioned VARCHAR(255),`

17+

18+

`-- Budget Signals`

19+

`budget_mentioned VARCHAR(100), -- "$300/month", "under $200"`

20+

`budget_amount DECIMAL(10,2),`

Show full diff (205 more lines)

●

Write/home/user/redditharbor/core/lead\_pipeline\_integration.py

└

1+

`#!/usr/bin/env python3`

2+

`"""`

3+

`Lead Pipeline Integration`

4+

`Shows exactly how to add lead extraction to your existing DLT pipeline.`

5+

6+

`This is a drop-in integration - minimal changes to existing code.`

7+

`"""`

8+

9+

`import sys`

10+

`from pathlib import Path`

11+

`from typing import Any`

12+

13+

`# Add project root`

14+

`project_root = Path(__file__).parent.parent`

15+

`if str(project_root) not in sys.path:`

16+

`sys.path.insert(0, str(project_root))`

17+

18+

`from core.lead_extractor import (`

19+

`LeadExtractor,`

20+

`convert_to_database_record,`

Show full diff (388 more lines)

●

Update Todos

└

☐ Build lead extraction module

☐ Create integration with existing pipeline

☐ Add customer\_leads table migration

☐ Creating demo script with examples

☐ Commit all changes

●

Write/home/user/redditharbor/scripts/demo\_lead\_extraction.py

└

1+

`#!/usr/bin/env python3`

2+

`"""`

3+

`Demo: Lead Extraction from Existing Data`

4+

5+

`This script proves that you ALREADY HAVE lead data in your database.`

6+

`It extracts leads from your app_opportunities_trust table and shows you:`

7+

8+

`1. Reddit usernames (the actual leads!)`

9+

`2. Budget mentions`

10+

`3. Competitor mentions`

11+

`4. Team sizes`

12+

`5. Buying intent signals`

13+

14+

`RUN THIS to see the blind spot removed in real-time.`

15+

`"""`

16+

17+

`import os`

18+

`import sys`

19+

`from pathlib import Path`

20+

Show full diff (259 more lines)

●

Bashpython scripts/demo\_lead\_extraction.py 2>&1 | head -150

└

Traceback (most recent call last): File "/home/user/redditharbor/scripts/demo\_lead\_extraction.py", line 25, in <module> from dotenv import load\_dotenv ModuleNotFoundError: No module named 'dotenv'

●

Bashpython core/lead\_extractor.py 2>&1 | head -200

└

\================================================================================ EXTRACTION COMPLETE ================================================================================... +142 linhas

\================================================================================ LEAD EXTRACTION DEMO ================================================================================ ================================================================================ EXAMPLE 1: Switching from Asana - need recommendations ================================================================================ 🔥 HIGH URGENCY LEAD - Posted 2024-01-15 16:02 \*\*Reddit:\*\* u/startup\_cto\_42 \*\*Subreddit:\*\* r/projectmanagement \*\*Problem:\*\* Switching from Asana - need recommendations... \*\*Currently Using:\*\* Asana \*\*Budget:\*\* ✅ $360/month (approved) \*\*Team Size:\*\* 12 users \*\*Timeline:\*\* end of Q1 \*\*Stage:\*\* 💰 Ready To Buy \*\*Pain Points:\*\* pricing \*\*Needs:\*\* recommendations We're a team of 12 and currently paying $360/month for Asana \*\*Lead Score:\*\* 85/100 \*\*View Post:\*\* https://reddit.com/r/projectmanagement/comments/abc123 ──────────────────────────────────────────────────────────────────────────────── DATABASE RECORD: ──────────────────────────────────────────────────────────────────────────────── reddit\_username: startup\_cto\_42 reddit\_post\_id: abc123 reddit\_post\_url: https://reddit.com/r/projectmanagement/comments/abc123 problem\_description: Switching from Asana - need recommendations full\_text: We're a team of 12 and currently paying $360/month for Asana. It's gotten too expensive after the latest pricing change. Looking for alternatives that: - Cost under $200/month - Integrate with Slack - Have good mobile apps Our budget is approved, need to decide by end of Q1. Any recommendations? current\_solution: Asana competitor\_mentioned: Asana budget\_mentioned: $360/month budget\_amount: 360.0 budget\_period: month budget\_status: approved team\_size: 12 company\_indicators: \['team\_reference'\] decision\_maker\_likely: False buying\_intent\_stage: ready\_to\_buy urgency\_level: high timeline\_mentioned: end of Q1 pain\_points: \['pricing'\] feature\_requirements: \["recommendations We're a team of 12 and currently paying $360/month for Asana", 'decide by end of Q1'\] subreddit: projectmanagement posted\_at: 2024-01-15 16:02:47 lead\_score: 85.0 lead\_status: new ================================================================================ EXAMPLE 2: MyFitnessPal alternatives? ================================================================================ ⚡ MEDIUM URGENCY LEAD - Posted 2024-01-15 16:02 \*\*Reddit:\*\* u/fitness\_enthusiast \*\*Subreddit:\*\* r/fitness \*\*Problem:\*\* MyFitnessPal alternatives?... \*\*Currently Using:\*\* MyFitnessPal \*\*Budget:\*\* 💵 $10/month (mentioned) \*\*Stage:\*\* 🔍 Evaluation \*\*Pain Points:\*\* pricing \*\*Needs:\*\* something that tracks macros properly and syncs with Apple Watch \*\*Lead Score:\*\* 85/100 \*\*View Post:\*\* https://reddit.com/r/fitness/comments/def456 ──────────────────────────────────────────────────────────────────────────────── DATABASE RECORD: ──────────────────────────────────────────────────────────────────────────────── reddit\_username: fitness\_enthusiast reddit\_post\_id: def456 reddit\_post\_url: https://reddit.com/r/fitness/comments/def456 problem\_description: MyFitnessPal alternatives? full\_text: I'm so frustrated with MyFitnessPal. The free version is too limited and $10/month for premium is expensive. Looking for something that tracks macros properly and syncs with Apple Watch. Budget is around $5-8/month max. current\_solution: MyFitnessPal competitor\_mentioned: MyFitnessPal budget\_mentioned: $10/month budget\_amount: 10.0 budget\_period: month budget\_status: mentioned decision\_maker\_likely: False buying\_intent\_stage: evaluation urgency\_level: medium pain\_points: \['pricing'\] feature\_requirements: \['something that tracks\\n macros properly and syncs with Apple Watch'\] subreddit: fitness posted\_at: 2024-01-15 16:02:47 lead\_score: 85.0 lead\_status: new ================================================================================ EXAMPLE 3: What CRM do you use? ================================================================================ 📋 LOW URGENCY LEAD - Posted 2024-01-15 16:02 \*\*Reddit:\*\* u/small\_biz\_owner \*\*Subreddit:\*\* r/smallbusiness \*\*Problem:\*\* What CRM do you use?... \*\*Currently Using:\*\* Salesforce \*\*Stage:\*\* 👀 Awareness \*\*Lead Score:\*\* 85/100 \*\*View Post:\*\* https://reddit.com/r/smallbusiness/comments/ghi789 ──────────────────────────────────────────────────────────────────────────────── DATABASE RECORD: ──────────────────────────────────────────────────────────────────────────────── reddit\_username: small\_biz\_owner reddit\_post\_id: ghi789 reddit\_post\_url: https://reddit.com/r/smallbusiness/comments/ghi789 problem\_description: What CRM do you use? full\_text: Small business owner here. Curious what CRM tools people use for managing customer relationships. Salesforce seems overkill for us.
