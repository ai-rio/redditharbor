-- Calculate Market Demand Score (0-10 scale)
-- Based on Reddit engagement metrics: comment count, upvote ratio, and score
-- Formula: (comment_score + upvote_score + score_score) / 3

CREATE OR REPLACE FUNCTION calculate_market_demand(p_submission_id UUID)
RETURNS FLOAT AS $$
DECLARE
  v_comment_count INT;
  v_upvote_ratio FLOAT;
  v_score INT;
  v_comment_score FLOAT := 0;
  v_upvote_score FLOAT := 0;
  v_score_score FLOAT := 0;
  v_market_demand FLOAT;
BEGIN
  -- Get submission metrics
  SELECT
    COALESCE(c.comment_count, 0),
    COALESCE(s.upvote_ratio, 0.5),
    COALESCE(s.score, 0)
  INTO v_comment_count, v_upvote_ratio, v_score
  FROM submissions s
  LEFT JOIN (
    SELECT submission_id, COUNT(*) as comment_count
    FROM comments
    GROUP BY submission_id
  ) c ON s.id = c.submission_id
  WHERE s.id = p_submission_id;

  -- Handle NULL submission (not found)
  IF v_comment_count IS NULL THEN
    RETURN 0;
  END IF;

  -- Score 1: Comment Count (0-10 scale)
  -- 100+ comments = 10, 50-99 = 7, 20-49 = 5, 5-19 = 3, <5 = 1
  CASE
    WHEN v_comment_count >= 100 THEN v_comment_score := 10;
    WHEN v_comment_count >= 50 THEN v_comment_score := 7;
    WHEN v_comment_count >= 20 THEN v_comment_score := 5;
    WHEN v_comment_count >= 5 THEN v_comment_score := 3;
    ELSE v_comment_score := 1;
  END CASE;

  -- Score 2: Upvote Ratio (0-10 scale)
  -- Ratio of upvotes to total votes. Higher ratio = more audience agreement
  -- 0.8+ = 9, 0.7-0.79 = 7, 0.6-0.69 = 5, 0.5-0.59 = 3, <0.5 = 1
  CASE
    WHEN v_upvote_ratio >= 0.8 THEN v_upvote_score := 9;
    WHEN v_upvote_ratio >= 0.7 THEN v_upvote_score := 7;
    WHEN v_upvote_ratio >= 0.6 THEN v_upvote_score := 5;
    WHEN v_upvote_ratio >= 0.5 THEN v_upvote_score := 3;
    ELSE v_upvote_score := 1;
  END CASE;

  -- Score 3: Raw Score (0-10 scale)
  -- Total upvotes (Reddit score). Indicates broader appeal
  -- 500+ = 10, 300-499 = 8, 100-299 = 6, 50-99 = 4, <50 = 2
  CASE
    WHEN v_score >= 500 THEN v_score_score := 10;
    WHEN v_score >= 300 THEN v_score_score := 8;
    WHEN v_score >= 100 THEN v_score_score := 6;
    WHEN v_score >= 50 THEN v_score_score := 4;
    ELSE v_score_score := 2;
  END CASE;

  -- Calculate final market demand as average of three components
  v_market_demand := (v_comment_score + v_upvote_score + v_score_score) / 3.0;

  -- Ensure result is within bounds
  RETURN LEAST(10.0, GREATEST(0.0, v_market_demand));
END;
$$ LANGUAGE plpgsql STABLE;

-- Create index on comments for performance
CREATE INDEX IF NOT EXISTS idx_comments_submission_id ON comments(submission_id);

COMMENT ON FUNCTION calculate_market_demand(UUID) IS
'Calculates market demand score (0-10 scale) based on comment count, upvote ratio, and score.
Higher scores indicate more market interest and audience engagement.';
