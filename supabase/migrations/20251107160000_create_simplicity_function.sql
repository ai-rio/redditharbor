-- Calculate Simplicity Score (0-10 scale)
-- Measures how simple/straightforward the problem is to solve
-- Based on technical complexity indicators and scope

CREATE OR REPLACE FUNCTION calculate_simplicity_score(p_submission_id UUID)
RETURNS FLOAT AS $$
DECLARE
  v_title TEXT;
  v_selftext TEXT;
  v_combined TEXT;
  v_simplicity_score FLOAT := 0;
  v_complexity_keywords INT := 0;
  v_scope_size INT;
BEGIN
  -- Get submission content
  SELECT COALESCE(s.title, '') || ' ' || COALESCE(s.selftext, ''),
         LENGTH(COALESCE(s.selftext, ''))
  INTO v_combined, v_scope_size
  FROM submissions s
  WHERE s.id = p_submission_id;

  -- Handle NULL submission
  IF v_combined IS NULL OR v_combined = '' THEN
    RETURN 0;
  END IF;

  -- Convert to lowercase
  v_combined := LOWER(v_combined);

  -- Count high-complexity keywords (reduce simplicity score)
  v_complexity_keywords := 0;
  v_complexity_keywords := v_complexity_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'complex', ''))) / 8;
  v_complexity_keywords := v_complexity_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'architecture', ''))) / 12;
  v_complexity_keywords := v_complexity_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'distributed', ''))) / 11;
  v_complexity_keywords := v_complexity_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'scalability', ''))) / 11;
  v_complexity_keywords := v_complexity_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'machine learning', ''))) / 16;
  v_complexity_keywords := v_complexity_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'quantum', ''))) / 8;
  v_complexity_keywords := v_complexity_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'blockchain', ''))) / 10;
  v_complexity_keywords := v_complexity_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'neural', ''))) / 7;
  v_complexity_keywords := v_complexity_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'algorithm', ''))) / 10;
  v_complexity_keywords := v_complexity_keywords + (LENGTH(v_combined) - LENGTH(REPLACE(v_combined, 'infrastructure', ''))) / 14;

  -- Assessment based on scope and complexity
  -- Larger posts (more text) suggest more complex problems
  -- Shorter, focused problems tend to be simpler
  IF v_scope_size < 500 THEN
    v_simplicity_score := 8;  -- Short, focused problems are simpler
  ELSIF v_scope_size < 1500 THEN
    v_simplicity_score := 6;  -- Medium-length problems
  ELSIF v_scope_size < 3000 THEN
    v_simplicity_score := 4;  -- Long posts suggest more complexity
  ELSE
    v_simplicity_score := 2;  -- Very long posts usually indicate complex problems
  END IF;

  -- Reduce score based on complexity keywords
  v_simplicity_score := v_simplicity_score - LEAST(v_simplicity_score, v_complexity_keywords * 0.5);

  -- Ensure result is within bounds
  RETURN LEAST(10.0, GREATEST(0.0, v_simplicity_score));
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION calculate_simplicity_score(UUID) IS
'Calculates simplicity score (0-10 scale) based on technical complexity indicators and problem scope.
Higher scores indicate simpler problems that are more likely to be solvable quickly with fewer resources.';
