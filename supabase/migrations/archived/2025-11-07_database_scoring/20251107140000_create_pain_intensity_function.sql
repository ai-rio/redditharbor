-- Calculate Pain Intensity Score (0-10 scale)
-- Measures the severity and urgency of the problem being discussed
-- Based on keyword frequency, emotional language, and sentiment

CREATE OR REPLACE FUNCTION calculate_pain_intensity(p_submission_id UUID)
RETURNS FLOAT AS $$
DECLARE
  v_title TEXT;
  v_selftext TEXT;
  v_combined TEXT;
  v_pain_score FLOAT := 0;
  v_keyword_count INT := 0;
BEGIN
  -- Get submission content
  SELECT COALESCE(s.title, '') || ' ' || COALESCE(s.selftext, '')
  INTO v_combined
  FROM submissions s
  WHERE s.id = p_submission_id;

  -- Handle NULL submission (not found)
  IF v_combined IS NULL OR v_combined = '' THEN
    RETURN 0;
  END IF;

  -- Convert to lowercase for case-insensitive matching
  v_combined := LOWER(v_combined);

  -- Count pain/problem keywords
  v_keyword_count := 0;

  -- High-intensity pain keywords (each worth ~1 point)
  v_keyword_count := v_keyword_count + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'struggling', ''))) / 10;
  v_keyword_count := v_keyword_count + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'desperate', ''))) / 9;
  v_keyword_count := v_keyword_count + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'urgent', ''))) / 7;
  v_keyword_count := v_keyword_count + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'crisis', ''))) / 6;
  v_keyword_count := v_keyword_count + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'failure', ''))) / 8;

  -- Medium-intensity pain keywords (each worth ~0.5 point)
  v_keyword_count := v_keyword_count + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'difficult', ''))) / 9 * 0.5;
  v_keyword_count := v_keyword_count + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'problem', ''))) / 8 * 0.5;
  v_keyword_count := v_keyword_count + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'pain', ''))) / 5 * 0.5;
  v_keyword_count := v_keyword_count + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'frustrated', ''))) / 10 * 0.5;
  v_keyword_count := v_keyword_count + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'challenge', ''))) / 10 * 0.5;

  -- Low-intensity pain keywords (each worth ~0.25 point)
  v_keyword_count := v_keyword_count + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'issue', ''))) / 6 * 0.25;
  v_keyword_count := v_keyword_count + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'bug', ''))) / 4 * 0.25;
  v_keyword_count := v_keyword_count + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'help', ''))) / 5 * 0.25;

  -- Scale keyword count to 0-10 range
  -- 20+ keywords = 10, 15-19 = 8, 10-14 = 6, 5-9 = 4, 1-4 = 2, 0 = 1
  CASE
    WHEN v_keyword_count >= 20 THEN v_pain_score := 10;
    WHEN v_keyword_count >= 15 THEN v_pain_score := 8;
    WHEN v_keyword_count >= 10 THEN v_pain_score := 6;
    WHEN v_keyword_count >= 5 THEN v_pain_score := 4;
    WHEN v_keyword_count >= 1 THEN v_pain_score := 2;
    ELSE v_pain_score := 1;
  END CASE;

  -- Ensure result is within bounds
  RETURN LEAST(10.0, GREATEST(0.0, v_pain_score));
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION calculate_pain_intensity(UUID) IS
'Calculates pain intensity score (0-10 scale) based on problem keywords and emotional language in the submission.
Higher scores indicate more urgent/severe problems that users are experiencing.';
