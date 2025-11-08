-- Calculate Monetization Potential Score (0-10 scale)
-- Measures the likelihood that solving this problem could be profitable
-- Based on market signals, payment mentions, and business context

CREATE OR REPLACE FUNCTION calculate_monetization_potential(p_submission_id UUID)
RETURNS FLOAT AS $$
DECLARE
  v_title TEXT;
  v_selftext TEXT;
  v_combined TEXT;
  v_monetization_score FLOAT := 0;
  v_payment_keywords INT := 0;
  v_business_keywords INT := 0;
  v_frequency INT := 0;
  v_subreddit TEXT;
BEGIN
  -- Get submission content and subreddit
  SELECT COALESCE(s.title, '') || ' ' || COALESCE(s.selftext, ''),
         COALESCE(s.subreddit, '')
  INTO v_combined, v_subreddit
  FROM submissions s
  WHERE s.id = p_submission_id;

  -- Handle NULL submission
  IF v_combined IS NULL OR v_combined = '' THEN
    RETURN 0;
  END IF;

  -- Convert to lowercase
  v_combined := LOWER(v_combined);

  -- Count payment/monetization keywords
  v_payment_keywords := 0;
  v_payment_keywords := v_payment_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'pay', ''))) / 4;
  v_payment_keywords := v_payment_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'cost', ''))) / 5;
  v_payment_keywords := v_payment_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'price', ''))) / 6;
  v_payment_keywords := v_payment_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'paid', ''))) / 5;
  v_payment_keywords := v_payment_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'subscription', ''))) / 12;
  v_payment_keywords := v_payment_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'revenue', ''))) / 8;
  v_payment_keywords := v_payment_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'profit', ''))) / 7;
  v_payment_keywords := v_payment_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'business', ''))) / 9;
  v_payment_keywords := v_payment_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'commercial', ''))) / 11;

  -- Count business context keywords
  v_business_keywords := 0;
  v_business_keywords := v_business_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'startup', ''))) / 8;
  v_business_keywords := v_business_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'market', ''))) / 7;
  v_business_keywords := v_business_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'customer', ''))) / 9;
  v_business_keywords := v_business_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'demand', ''))) / 7;
  v_business_keywords := v_business_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'industry', ''))) / 9;
  v_business_keywords := v_business_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'service', ''))) / 8;
  v_business_keywords := v_business_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'product', ''))) / 8;

  -- Subreddit context (finance-related subreddits have higher monetization potential)
  v_frequency := 0;
  IF v_subreddit IN ('personalfinance', 'investing', 'stocks', 'Bogleheads',
                      'financialindependence', 'CryptoCurrency', 'tax', 'Accounting',
                      'RealEstateInvesting', 'FinancialCareers', 'entrepreneurs', 'startups',
                      'freelance', 'SideHustle') THEN
    v_frequency := v_frequency + 2;  -- Finance/business subreddits boost score
  ELSIF v_subreddit IN ('fitness', 'loseit', 'bodyweightfitness', 'nutrition', 'keto',
                         'running', 'cycling', 'yoga', 'meditation', 'mentalhealth',
                         'fitness30plus', 'homegym') THEN
    v_frequency := v_frequency + 1;  -- Health subreddits have some monetization potential
  END IF;

  -- Calculate final score: balance between explicit payment mentions and business context
  v_monetization_score := (v_payment_keywords + v_business_keywords + v_frequency) / 3.0;

  -- Ensure result is within bounds
  RETURN LEAST(10.0, GREATEST(0.0, v_monetization_score));
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION calculate_monetization_potential(UUID) IS
'Calculates monetization potential score (0-10 scale) based on payment mentions, business keywords, and subreddit context.
Higher scores indicate problems that are more likely to have profitable solutions.';
