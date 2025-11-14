-- Customer Leads Table for Option B (Lead Generation)
-- This table stores Reddit users as sales leads (not app ideas)

-- ============================================================================
-- CUSTOMER LEADS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS customer_leads (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Lead Identification (THE ACTUAL LEAD!)
  reddit_username VARCHAR(255) NOT NULL,
  reddit_post_id TEXT NOT NULL,
  reddit_post_url TEXT,

  -- Problem Context
  problem_description TEXT NOT NULL,
  full_text TEXT,
  current_solution VARCHAR(255), -- "Asana", "MyFitnessPal", etc.
  competitor_mentioned VARCHAR(255),

  -- Budget Signals
  budget_mentioned VARCHAR(100), -- "$300/month", "under $200"
  budget_amount DECIMAL(10,2),
  budget_period VARCHAR(20), -- month, year
  budget_status VARCHAR(50), -- mentioned, approved, constrained, unknown

  -- Company/Team Indicators
  team_size INTEGER,
  company_indicators JSONB, -- ["team_reference", "decision_maker", etc.]
  decision_maker_likely BOOLEAN DEFAULT FALSE,

  -- Buying Intent
  buying_intent_stage VARCHAR(50) NOT NULL, -- awareness, evaluation, ready_to_buy
  urgency_level VARCHAR(20) NOT NULL, -- low, medium, high, critical
  timeline_mentioned VARCHAR(100),

  -- Pain Points & Requirements
  pain_points JSONB, -- ["pricing", "performance", "features"]
  feature_requirements JSONB, -- Array of requirement strings

  -- Context
  subreddit VARCHAR(100) NOT NULL,
  posted_at TIMESTAMP WITH TIME ZONE,

  -- Scoring & Status
  lead_score DECIMAL(5,2), -- 0-100
  lead_status VARCHAR(50) DEFAULT 'new', -- new, contacted, qualified, won, lost

  -- Assignment (for multi-tenant)
  assigned_to_company_id UUID, -- References customer_companies(id)
  assigned_at TIMESTAMP WITH TIME ZONE,
  contacted_at TIMESTAMP WITH TIME ZONE,

  -- Metadata
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Constraints
  CONSTRAINT chk_lead_score CHECK (lead_score >= 0 AND lead_score <= 100),
  CONSTRAINT chk_budget_amount CHECK (budget_amount IS NULL OR budget_amount >= 0)
);

-- Indexes for performance
CREATE INDEX idx_customer_leads_username ON customer_leads(reddit_username);
CREATE INDEX idx_customer_leads_post_id ON customer_leads(reddit_post_id);
CREATE INDEX idx_customer_leads_subreddit ON customer_leads(subreddit);
CREATE INDEX idx_customer_leads_competitor ON customer_leads(competitor_mentioned);
CREATE INDEX idx_customer_leads_buying_stage ON customer_leads(buying_intent_stage);
CREATE INDEX idx_customer_leads_urgency ON customer_leads(urgency_level);
CREATE INDEX idx_customer_leads_lead_score ON customer_leads(lead_score DESC);
CREATE INDEX idx_customer_leads_lead_status ON customer_leads(lead_status);
CREATE INDEX idx_customer_leads_assigned_company ON customer_leads(assigned_to_company_id);
CREATE INDEX idx_customer_leads_posted_at ON customer_leads(posted_at DESC);

-- Unique constraint on Reddit post (one lead per post)
CREATE UNIQUE INDEX idx_customer_leads_unique_post ON customer_leads(reddit_post_id);

-- ============================================================================
-- CUSTOMER COMPANIES TABLE (Multi-Tenant for Option B)
-- ============================================================================

CREATE TABLE IF NOT EXISTS customer_companies (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Company Info
  company_name VARCHAR(255) NOT NULL,
  industry VARCHAR(100),
  website VARCHAR(255),

  -- Subscription
  subscription_tier VARCHAR(50), -- starter, growth, enterprise
  subscription_status VARCHAR(50) DEFAULT 'active', -- active, trial, cancelled
  monthly_price DECIMAL(10,2),

  -- Monitoring Config
  monitored_keywords JSONB, -- ["Asana alternatives", "project management"]
  monitored_subreddits JSONB, -- ["projectmanagement", "startups"]
  competitor_names JSONB, -- ["Asana", "Monday.com", "ClickUp"]

  -- Alert Preferences
  slack_webhook_url TEXT,
  email_notifications JSONB, -- ["user1@company.com", "user2@company.com"]
  alert_frequency VARCHAR(50) DEFAULT 'realtime', -- realtime, daily, weekly

  -- Integration Config
  crm_integration VARCHAR(50), -- salesforce, hubspot, pipedrive
  crm_config JSONB,

  -- Usage Stats
  leads_received_this_month INTEGER DEFAULT 0,
  leads_contacted INTEGER DEFAULT 0,
  leads_won INTEGER DEFAULT 0,
  total_leads_lifetime INTEGER DEFAULT 0,

  -- Metadata
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_alert_sent_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_customer_companies_name ON customer_companies(company_name);
CREATE INDEX idx_customer_companies_tier ON customer_companies(subscription_tier);
CREATE INDEX idx_customer_companies_status ON customer_companies(subscription_status);

-- ============================================================================
-- USEFUL VIEWS
-- ============================================================================

-- Hot Leads (high priority, ready to contact)
CREATE OR REPLACE VIEW hot_leads AS
SELECT
  cl.*,
  cc.company_name,
  cc.slack_webhook_url
FROM customer_leads cl
LEFT JOIN customer_companies cc ON cl.assigned_to_company_id = cc.id
WHERE
  cl.lead_status = 'new'
  AND cl.lead_score >= 70
  AND cl.urgency_level IN ('high', 'critical')
  AND cl.buying_intent_stage IN ('evaluation', 'ready_to_buy')
ORDER BY cl.lead_score DESC, cl.posted_at DESC;

-- Leads by Competitor
CREATE OR REPLACE VIEW leads_by_competitor AS
SELECT
  competitor_mentioned,
  COUNT(*) as lead_count,
  AVG(lead_score) as avg_lead_score,
  COUNT(CASE WHEN buying_intent_stage = 'ready_to_buy' THEN 1 END) as ready_to_buy_count,
  COUNT(CASE WHEN urgency_level IN ('high', 'critical') THEN 1 END) as high_urgency_count
FROM customer_leads
WHERE competitor_mentioned IS NOT NULL
GROUP BY competitor_mentioned
ORDER BY lead_count DESC;

-- Lead Funnel Metrics
CREATE OR REPLACE VIEW lead_funnel_metrics AS
SELECT
  DATE_TRUNC('day', posted_at) as date,
  COUNT(*) as total_leads,
  COUNT(CASE WHEN lead_status = 'new' THEN 1 END) as new_leads,
  COUNT(CASE WHEN lead_status = 'contacted' THEN 1 END) as contacted_leads,
  COUNT(CASE WHEN lead_status = 'qualified' THEN 1 END) as qualified_leads,
  COUNT(CASE WHEN lead_status = 'won' THEN 1 END) as won_leads,
  AVG(lead_score) as avg_lead_score
FROM customer_leads
WHERE posted_at IS NOT NULL
GROUP BY DATE_TRUNC('day', posted_at)
ORDER BY date DESC;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE customer_leads IS 'Sales leads extracted from Reddit posts (Option B)';
COMMENT ON TABLE customer_companies IS 'SaaS customers using RedditHarbor for lead generation (multi-tenant)';

COMMENT ON COLUMN customer_leads.reddit_username IS 'The actual lead - Reddit user to contact';
COMMENT ON COLUMN customer_leads.budget_mentioned IS 'Budget signals extracted from post';
COMMENT ON COLUMN customer_leads.buying_intent_stage IS 'awareness → evaluation → ready_to_buy';
COMMENT ON COLUMN customer_leads.lead_score IS 'Quality score from opportunity_analyzer_agent (0-100)';
COMMENT ON COLUMN customer_companies.monitored_keywords IS 'Keywords to monitor for this customer';

-- ============================================================================
-- SAMPLE QUERY EXAMPLES
-- ============================================================================

-- Find high-value B2B leads with budget and urgency
-- SELECT * FROM customer_leads
-- WHERE lead_score >= 75
--   AND budget_amount >= 100
--   AND urgency_level IN ('high', 'critical')
--   AND team_size >= 10
-- ORDER BY lead_score DESC;

-- Find leads mentioning specific competitor
-- SELECT * FROM customer_leads
-- WHERE competitor_mentioned = 'Asana'
--   AND buying_intent_stage IN ('evaluation', 'ready_to_buy')
-- ORDER BY posted_at DESC;

-- Get competitive intelligence for a category
-- SELECT * FROM leads_by_competitor
-- WHERE competitor_mentioned LIKE '%management%';
