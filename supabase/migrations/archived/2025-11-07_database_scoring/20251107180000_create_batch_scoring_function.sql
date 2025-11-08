-- Batch scoring function for all submissions
-- Efficiently scores all submissions and populates opportunity_scores table

CREATE OR REPLACE FUNCTION score_all_submissions()
RETURNS TABLE(
  total_submissions INT,
  scored_submissions INT,
  avg_composite_score FLOAT,
  highest_score FLOAT,
  lowest_score FLOAT
) AS $$
DECLARE
  v_total_count INT;
  v_scored_count INT;
  v_avg_score FLOAT;
  v_highest FLOAT;
  v_lowest FLOAT;
BEGIN
  -- Get total submission count
  SELECT COUNT(*) INTO v_total_count FROM submissions;

  -- Score all submissions that don't have scores yet
  -- Use a temporary table to track processed submissions
  WITH submissions_to_score AS (
    SELECT s.id
    FROM submissions s
    LEFT JOIN opportunity_scores os ON s.id = os.submission_id
    WHERE os.id IS NULL
  )
  INSERT INTO opportunity_scores (
    submission_id,
    market_demand,
    pain_intensity,
    monetization_potential,
    simplicity_score,
    composite_score,
    calculation_version
  )
  SELECT
    s.id,
    calculate_market_demand(s.id),
    calculate_pain_intensity(s.id),
    calculate_monetization_potential(s.id),
    calculate_simplicity_score(s.id),
    calculate_composite_score(s.id),
    1
  FROM submissions s
  WHERE s.id IN (SELECT id FROM submissions_to_score);

  -- Count newly scored submissions
  SELECT COUNT(*) INTO v_scored_count FROM opportunity_scores;

  -- Calculate statistics
  SELECT
    AVG(composite_score),
    MAX(composite_score),
    MIN(composite_score)
  INTO v_avg_score, v_highest, v_lowest
  FROM opportunity_scores;

  -- Return results
  RETURN QUERY SELECT v_total_count, v_scored_count, v_avg_score, v_highest, v_lowest;
END;
$$ LANGUAGE plpgsql;

-- Function to score a batch of submissions by ID
CREATE OR REPLACE FUNCTION score_submissions_batch(p_submission_ids UUID[])
RETURNS TABLE(
  scored_count INT,
  avg_score FLOAT,
  min_score FLOAT,
  max_score FLOAT,
  execution_time_ms INT
) AS $$
DECLARE
  v_start_time TIMESTAMP;
  v_scored_count INT := 0;
  v_submission_id UUID;
  i INT;
  v_avg_score FLOAT;
  v_min_score FLOAT;
  v_max_score FLOAT;
BEGIN
  v_start_time := NOW();

  -- Score each submission in the batch
  FOREACH v_submission_id IN ARRAY p_submission_ids
  LOOP
    PERFORM update_opportunity_score(v_submission_id);
    v_scored_count := v_scored_count + 1;
  END LOOP;

  -- Calculate statistics for the batch
  SELECT
    AVG(composite_score),
    MIN(composite_score),
    MAX(composite_score)
  INTO v_avg_score, v_min_score, v_max_score
  FROM opportunity_scores
  WHERE submission_id = ANY(p_submission_ids);

  -- Return results
  RETURN QUERY SELECT
    v_scored_count,
    v_avg_score,
    v_min_score,
    v_max_score,
    EXTRACT(EPOCH FROM (NOW() - v_start_time))::INT * 1000;
END;
$$ LANGUAGE plpgsql;

-- Function to get top opportunities by composite score
CREATE OR REPLACE FUNCTION get_top_opportunities(p_limit INT DEFAULT 10, p_min_score FLOAT DEFAULT 0)
RETURNS TABLE(
  submission_id UUID,
  title TEXT,
  composite_score FLOAT,
  market_demand FLOAT,
  pain_intensity FLOAT,
  monetization_potential FLOAT,
  simplicity_score FLOAT,
  score_rank INT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    s.id,
    s.title,
    os.composite_score,
    os.market_demand,
    os.pain_intensity,
    os.monetization_potential,
    os.simplicity_score,
    ROW_NUMBER() OVER (ORDER BY os.composite_score DESC)::INT
  FROM submissions s
  JOIN opportunity_scores os ON s.id = os.submission_id
  WHERE os.composite_score >= p_min_score
  ORDER BY os.composite_score DESC
  LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION score_all_submissions() IS
'Batch scores all submissions that haven''t been scored yet.
Returns statistics about the scoring operation and overall scores.';

COMMENT ON FUNCTION score_submissions_batch(UUID[]) IS
'Scores a specific batch of submissions by their IDs.
Useful for incremental scoring of new submissions.';

COMMENT ON FUNCTION get_top_opportunities(INT, FLOAT) IS
'Returns the top opportunities sorted by composite score.
Useful for identifying the best opportunities to pursue.';
