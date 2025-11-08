-- Calculate Composite Opportunity Score (0-100 scale)
-- Master function that combines all component scores with weights:
-- - Market Demand: 35% (how many people want this solved)
-- - Pain Intensity: 30% (how urgent/critical the problem is)
-- - Monetization: 20% (how profitable the solution could be)
-- - Simplicity: 15% (how easy it is to build a solution)

CREATE OR REPLACE FUNCTION calculate_composite_score(p_submission_id UUID)
RETURNS FLOAT AS $$
DECLARE
  v_market_demand FLOAT;
  v_pain_intensity FLOAT;
  v_monetization FLOAT;
  v_simplicity FLOAT;
  v_composite FLOAT;
BEGIN
  -- Calculate individual component scores
  v_market_demand := calculate_market_demand(p_submission_id);
  v_pain_intensity := calculate_pain_intensity(p_submission_id);
  v_monetization := calculate_monetization_potential(p_submission_id);
  v_simplicity := calculate_simplicity_score(p_submission_id);

  -- Calculate weighted composite score (0-100 scale)
  -- Formula: (md*0.35 + pi*0.30 + mon*0.20 + simp*0.15) * 10
  v_composite := (
    (v_market_demand * 0.35) +
    (v_pain_intensity * 0.30) +
    (v_monetization * 0.20) +
    (v_simplicity * 0.15)
  ) * 10.0;

  -- Ensure result is within bounds
  RETURN LEAST(100.0, GREATEST(0.0, v_composite));
END;
$$ LANGUAGE plpgsql STABLE;

-- Create function to update an opportunity score record
CREATE OR REPLACE FUNCTION update_opportunity_score(p_submission_id UUID)
RETURNS TABLE(
  id UUID,
  submission_id UUID,
  market_demand FLOAT,
  pain_intensity FLOAT,
  monetization_potential FLOAT,
  simplicity_score FLOAT,
  composite_score FLOAT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
) AS $$
DECLARE
  v_md FLOAT;
  v_pi FLOAT;
  v_mp FLOAT;
  v_ss FLOAT;
  v_cs FLOAT;
BEGIN
  -- Calculate all scores
  v_md := calculate_market_demand(p_submission_id);
  v_pi := calculate_pain_intensity(p_submission_id);
  v_mp := calculate_monetization_potential(p_submission_id);
  v_ss := calculate_simplicity_score(p_submission_id);
  v_cs := calculate_composite_score(p_submission_id);

  -- Upsert into opportunity_scores table
  INSERT INTO opportunity_scores (
    submission_id,
    market_demand,
    pain_intensity,
    monetization_potential,
    simplicity_score,
    composite_score,
    calculation_version
  ) VALUES (
    p_submission_id,
    v_md,
    v_pi,
    v_mp,
    v_ss,
    v_cs,
    1
  )
  ON CONFLICT (submission_id) DO UPDATE SET
    market_demand = v_md,
    pain_intensity = v_pi,
    monetization_potential = v_mp,
    simplicity_score = v_ss,
    composite_score = v_cs,
    updated_at = NOW(),
    calculation_version = calculation_version + 1
  RETURNING
    opportunity_scores.id,
    opportunity_scores.submission_id,
    opportunity_scores.market_demand,
    opportunity_scores.pain_intensity,
    opportunity_scores.monetization_potential,
    opportunity_scores.simplicity_score,
    opportunity_scores.composite_score,
    opportunity_scores.created_at,
    opportunity_scores.updated_at
  INTO id, submission_id, market_demand, pain_intensity, monetization_potential, simplicity_score, composite_score, created_at, updated_at;

  RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_composite_score(UUID) IS
'Calculates composite opportunity score (0-100 scale) using weighted components:
- Market Demand (35%): How many people want this solved
- Pain Intensity (30%): How urgent/critical the problem is
- Monetization (20%): How profitable the solution could be
- Simplicity (15%): How easy it is to build a solution
Scores are designed to identify high-impact, achievable opportunities.';

COMMENT ON FUNCTION update_opportunity_score(UUID) IS
'Updates or inserts an opportunity score record for a submission.
Calculates all component scores and returns the result.';
