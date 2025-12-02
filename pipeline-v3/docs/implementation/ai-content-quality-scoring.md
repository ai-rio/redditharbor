# AI Content Quality Scoring

## Overview

The AI Content Quality Scoring system automatically evaluates Reddit submissions for content quality and spam detection. This feature enhances the opportunity analysis pipeline by filtering out low-quality content and providing quality metrics for better decision-making.

## Features

### Quality Scoring Components

1. **content_quality_score** (0-100, required)
   - 80-100: High quality, original content with clear value
   - 60-79: Good quality content with minor issues
   - 40-59: Moderate quality with several concerns
   - 0-39: Low quality, likely spam or irrelevant

2. **is_spam** (boolean, default: False)
   - Automatically determined based on content analysis
   - Uses multiple spam detection indicators

3. **spam_indicators** (list of strings, default: [])
   - Specific reasons why content was flagged as spam
   - Helps with debugging and transparency

### Spam Detection Criteria

Content is flagged as spam when it exhibits:

- **Excessive Capitalization**: >40% caps in title
- **Repetitive Content**: Same meaningful word repeated >3 times
- **Suspicious Links**: URL shorteners (bit.ly, tinyurl.com, etc.)
- **Spam Keywords**: "click here", "buy now", "free money", etc.
- **Content Length Issues**: <50 characters or >5000 characters
- **Poor Grammar**: Multiple exclamation marks, improper capitalization

## Implementation Details

### Model Changes

The `AnalysisResult` model now includes:

```python
# AI content quality scoring
content_quality_score: float = Field(
    ...,
    ge=0.0,
    le=100.0,
    description="AI-generated content quality score (0-100)"
)
is_spam: bool = Field(
    default=False,
    description="Whether the content is identified as spam"
)
spam_indicators: List[str] = Field(
    default_factory=list,
    description="List of spam indicators detected in the content"
)
```

### Quality Thresholds Validator

A critical validator ensures data consistency:

```python
@model_validator(mode='after')
def validate_quality_thresholds(self) -> 'AnalysisResult':
    """Validate quality thresholds: spam posts should have content_quality_score ≤ 40"""
    if self.is_spam and self.content_quality_score > 40.0:
        raise ValueError(
            f"Spam content must have content_quality_score ≤ 40. "
            f"Current: content_quality_score={self.content_quality_score}, is_spam={self.is_spam}"
        )
    return self
```

### Quality Analysis Algorithm

The `SimpleOpportunityAnalyzer` includes comprehensive quality analysis:

1. **Baseline Score**: Starts at 85.0 (high quality)
2. **Penalty System**: Deductions for each spam indicator:
   - Excessive caps: -15 points
   - Repetitive content: -20 points
   - Suspicious links: -25 points
   - Spam keywords: -20 points
   - Too short: -10 points
   - Too long: -15 points
   - Poor grammar: -10 points

3. **Spam Determination**: Content is spam if:
   - Quality score ≤ 40.0
   - OR has ≥3 spam indicators

## Usage Examples

### High Quality Content

```python
from models.analysis import AnalysisResult, AppIdea, MarketMetrics

# High quality submission
high_quality = AnalysisResult(
    submission_id="good_post_123",
    app_idea=app_idea,
    market_metrics=market_metrics,
    final_score=80.0,
    confidence_score=85.0,
    trust_level="HIGH",
    content_quality_score=92.5,  # High quality
    is_spam=False,
    spam_indicators=[]  # No spam indicators
)
```

### Spam Content

```python
# Spam submission
spam_analysis = AnalysisResult(
    submission_id="spam_post_456",
    app_idea=app_idea,
    market_metrics=market_metrics,
    final_score=15.0,
    confidence_score=25.0,
    trust_level="LOW",
    content_quality_score=20.0,  # Low quality for spam
    is_spam=True,
    spam_indicators=["excessive_caps", "spam_keywords", "too_short"]
)
```

### Validation Errors

```python
try:
    # This will fail validation - spam with high quality score
    invalid = AnalysisResult(
        submission_id="invalid_789",
        app_idea=app_idea,
        market_metrics=market_metrics,
        final_score=75.0,
        confidence_score=80.0,
        trust_level="HIGH",
        content_quality_score=85.0,  # Too high for spam
        is_spam=True
    )
except ValueError as e:
    print(f"Validation failed: {e}")
    # Output: Validation failed: Spam content must have content_quality_score ≤ 40. Current: content_quality_score=85.0, is_spam=True
```

## Integration with LLM Analysis

The `OpportunityAnalyzer` system prompt now includes quality scoring instructions:

```
CONTENT QUALITY SCORING REQUIREMENTS:
7. Assign a content_quality_score (0-100) where:
   - 80-100: High quality, original content with clear value
   - 60-79: Good quality content with minor issues
   - 40-59: Moderate quality with several concerns
   - 0-39: Low quality, likely spam or irrelevant

8. Set is_spam = True and content_quality_score ≤ 40 for:
   - Excessive capitalization or punctuation
   - Repetitive phrases or content
   - Suspicious links or URL shorteners
   - Common spam keywords
   - Very short content (< 50 chars) with no substance
   - Poor grammar or formatting

9. List specific spam_indicators when is_spam=True
```

## Testing

The quality scoring system includes comprehensive tests in `tests/test_models.py::TestAnalysisResultQuality`:

- Field validation tests
- Default value tests
- Quality threshold validator tests
- Complete workflow tests

### Running Tests

```bash
# Run quality scoring tests
./run_tests.sh -k "TestAnalysisResultQuality" -v

# Run all quality-related tests
./run_tests.sh -k "quality" -v
```

## Performance Considerations

- The quality analysis adds minimal overhead (<1ms per submission)
- Spam detection uses efficient string operations
- No external dependencies required for quality analysis
- LLM-powered analysis provides more sophisticated quality assessment

## Future Enhancements

Potential improvements to the quality scoring system:

1. **Machine Learning Models**: Train custom models for spam detection
2. **User Feedback Integration**: Learn from user spam reports
3. **Context-Aware Scoring**: Consider subreddit-specific norms
4. **Real-Time Adaptation**: Adjust thresholds based on usage patterns
5. **Advanced Linguistic Analysis**: Natural language processing for better quality assessment

## Configuration

The quality scoring system can be configured through:

- Spam keyword lists
- Quality score thresholds
- Penalty weights for different indicators
- Content length limits

These settings can be adjusted in `transform/analyzer.py` or moved to configuration files for easier management.

## Troubleshooting

### Common Issues

1. **Validation Errors**: Ensure `content_quality_score ≤ 40` when `is_spam=True`
2. **Missing Fields**: All three quality fields must be provided for new AnalysisResult objects
3. **Type Errors**: `spam_indicators` must be a list of strings

### Debug Mode

Enable detailed logging to see quality analysis process:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will show:
- Content quality analysis steps
- Spam indicator detection
- Score calculations
- Validation results

## API Documentation

### SimpleOpportunityAnalyzer.quality_analysis()

```python
def _analyze_content_quality(self, submission: RedditSubmission) -> tuple[float, bool, List[str]]:
    """
    Analyze content quality and detect spam indicators

    Args:
        submission: Reddit submission to analyze

    Returns:
        Tuple of (content_quality_score, is_spam, spam_indicators)
    """
```

### AnalysisResult.validate_quality_thresholds()

```python
@model_validator(mode='after')
def validate_quality_thresholds(self) -> 'AnalysisResult':
    """
    Validate quality thresholds: spam posts should have content_quality_score ≤ 40

    Raises:
        ValueError: If is_spam=True and content_quality_score > 40.0
    """
```

## Security Considerations

- Quality scoring does not store user data permanently
- Spam indicators are logged for debugging only
- No personal information is extracted or stored
- All analysis happens in memory without external data access

## Conclusion

The AI Content Quality Scoring system provides robust automated spam detection and content quality assessment for Reddit submissions. It enhances the reliability of opportunity analysis by filtering out low-quality content while maintaining high-quality insights for legitimate discussions.