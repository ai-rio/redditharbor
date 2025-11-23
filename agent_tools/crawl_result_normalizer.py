#!/usr/bin/env python3
"""
Crawl Result Normalizer: Ensures Consistent Output Across Crawlers

Standardizes outputs from different web crawlers (Jina AI, Crawl4AI) to ensure
consistent data format throughout the pipeline. Handles:

1. Content format normalization (markdown vs structured text)
2. Metadata extraction and standardization
3. Content cleaning and preprocessing
4. Quality assessment with consistent metrics
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class NormalizedCrawlResult:
    """Consistent result format across all crawlers"""
    # Core content
    content: str
    url: str
    title: str | None = None

    # Standardized metadata
    source_crawler: str = "unknown"
    extracted_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    word_count: int = 0
    char_count: int = 0

    # Quality metrics (normalized 0-1)
    content_quality_score: float = 0.0
    structure_score: float = 0.0  # How well-structured the content is
    completeness_score: float = 0.0  # How complete the content feels

    # Processing metadata
    processing_notes: list = field(default_factory=list)
    normalization_applied: bool = True

    def __post_init__(self):
        """Calculate derived metrics after initialization"""
        if self.word_count == 0:
            self.word_count = len(self.content.split())
        self.char_count = len(self.content)

        # Auto-calculate quality scores if not set
        if self.content_quality_score == 0:
            self.content_quality_score = self._calculate_content_quality()
        if self.structure_score == 0:
            self.structure_score = self._calculate_structure_score()
        if self.completeness_score == 0:
            self.completeness_score = self._calculate_completeness_score()

    def _calculate_content_quality(self) -> float:
        """Calculate content quality score based on various factors"""
        if not self.content:
            return 0.0

        score = 0.0

        # Length factor (prefer substantial content)
        length_score = min(1.0, len(self.content) / 1000)  # 1000 chars = 1.0
        score += length_score * 0.3

        # Word diversity (unique words / total words)
        words = self.content.split()
        if words:
            unique_words = set(word.lower() for word in words)
            diversity_score = len(unique_words) / len(words)
            score += diversity_score * 0.2

        # Sentence structure (has periods, proper punctuation)
        has_sentences = '.' in self.content and len(self.content) > 50
        sentence_score = 1.0 if has_sentences else 0.5
        score += sentence_score * 0.2

        # Readability (not too short, not too repetitive)
        if len(words) > 10:
            unique_words = set(word.lower() for word in words)
            repetition_penalty = min(0.3, (len(words) - len(unique_words)) / len(words))
            score += (1.0 - repetition_penalty) * 0.3

        return min(1.0, score)

    def _calculate_structure_score(self) -> float:
        """Calculate how well-structured the content is"""
        if not self.content:
            return 0.0

        score = 0.0

        # Has headers (markdown # or HTML headings)
        has_headers = bool(re.search(r'^#+\s+|^<h[1-6]>', self.content, re.MULTILINE))
        score += 0.3 if has_headers else 0.0

        # Has lists (markdown - or * or numbers)
        has_lists = bool(re.search(r'^\s*[-*+]\s+|^\s*\d+\.\s+', self.content, re.MULTILINE))
        score += 0.2 if has_lists else 0.0

        # Has links (markdown or HTML)
        has_links = bool(re.search(r'\[.*?\]\(.*?\)|<a\s+href=', self.content))
        score += 0.2 if has_links else 0.0

        # Has paragraphs (multiple lines with content)
        lines = [line.strip() for line in self.content.split('\n') if line.strip()]
        paragraph_score = min(1.0, len(lines) / 5)  # 5+ paragraphs = good structure
        score += paragraph_score * 0.3

        return min(1.0, score)

    def _calculate_completeness_score(self) -> float:
        """Calculate how complete the content feels"""
        if not self.content:
            return 0.0

        score = 0.5  # Base score

        # Has substantial content
        if len(self.content) > 200:
            score += 0.2
        if len(self.content) > 1000:
            score += 0.1

        # Has title (good sign of completeness)
        if self.title:
            score += 0.1

        # Has meaningful ending (conclusion, summary, etc.)
        ending_indicators = ['conclusion', 'summary', 'in conclusion', 'finally', 'in summary']
        if any(indicator in self.content.lower() for indicator in ending_indicators):
            score += 0.1

        return min(1.0, score)


class CrawlResultNormalizer:
    """
    Normalizes crawl results from different crawlers into consistent format
    """

    def __init__(self, strict_mode: bool = False):
        """
        Initialize normalizer

        Args:
            strict_mode: If True, applies stricter normalization rules
        """
        self.strict_mode = strict_mode
        self.normalization_stats = {
            "total_processed": 0,
            "jina_results": 0,
            "crawl4ai_results": 0,
            "normalizations_applied": 0
        }

    def normalize_result(
        self,
        raw_result: Any,
        source_crawler: str,
        url: str
    ) -> NormalizedCrawlResult:
        """
        Normalize a raw crawl result into consistent format

        Args:
            raw_result: Raw result from crawler (varies by type)
            source_crawler: Name of the crawler that produced this result
            url: Original URL that was crawled

        Returns:
            NormalizedCrawlResult with consistent format
        """
        self.normalization_stats["total_processed"] += 1

        # Track results by crawler type
        if source_crawler.lower() in ["jina_ai", "jina"]:
            self.normalization_stats["jina_results"] += 1
        elif source_crawler.lower() in ["crawl4ai", "crawl4"]:
            self.normalization_stats["crawl4ai_results"] += 1

        # Extract content based on crawler type
        if source_crawler.lower() in ["jina_ai", "jina"]:
            normalized = self._normalize_jina_result(raw_result, url)
        elif source_crawler.lower() in ["crawl4ai", "crawl4"]:
            normalized = self._normalize_crawl4ai_result(raw_result, url)
        else:
            # Fallback for unknown crawlers
            normalized = self._normalize_generic_result(raw_result, url, source_crawler)

        self.normalization_stats["normalizations_applied"] += 1
        return normalized

    def _normalize_jina_result(self, raw_result: Any, url: str) -> NormalizedCrawlResult:
        """Normalize Jina AI result format"""
        # Handle different Jina result formats
        if hasattr(raw_result, 'content'):
            # JinaResponse object
            content = raw_result.content
            title = getattr(raw_result, 'title', None)
            word_count = getattr(raw_result, 'word_count', 0)
        elif isinstance(raw_result, str):
            # Raw string response
            content = self._extract_jina_content_from_string(raw_result)
            title = self._extract_jina_title_from_string(raw_result)
            word_count = len(content.split())
        else:
            # Dictionary or other format
            content = str(raw_result)
            title = None
            word_count = len(content.split())

        # Clean Jina-specific metadata from content
        content = self._clean_jina_content(content)

        processing_notes = []
        if "Title:" in content or "URL Source:" in content:
            processing_notes.append("Removed Jina metadata headers")

        return NormalizedCrawlResult(
            content=content,
            url=url,
            title=title,
            source_crawler="jina_ai",
            word_count=word_count,
            processing_notes=processing_notes
        )

    def _normalize_crawl4ai_result(self, raw_result: Any, url: str) -> NormalizedCrawlResult:
        """Normalize Crawl4AI result format"""
        # Handle CrawlResult object from hybrid_crawler
        if hasattr(raw_result, 'content'):
            content = raw_result.content
            title = getattr(raw_result, 'title', None)
            word_count = getattr(raw_result, 'word_count', 0)
            success = getattr(raw_result, 'success', True)
        else:
            # Fallback for other formats
            content = str(raw_result)
            title = None
            word_count = len(content.split())
            success = True

        processing_notes = []
        if not success:
            processing_notes.append("Crawler reported failure")

        # Crawl4AI usually produces clean markdown, minimal processing needed
        content = self._clean_markdown_content(content)

        return NormalizedCrawlResult(
            content=content,
            url=url,
            title=title,
            source_crawler="crawl4ai",
            word_count=word_count,
            processing_notes=processing_notes
        )

    def _normalize_generic_result(self, raw_result: Any, url: str, source_crawler: str) -> NormalizedCrawlResult:
        """Fallback normalization for unknown crawler types"""
        content = str(raw_result)

        # Try to extract basic info
        lines = content.split('\n')
        title = lines[0] if lines and len(lines[0]) < 200 else None

        processing_notes = [f"Applied generic normalization for {source_crawler}"]

        return NormalizedCrawlResult(
            content=content,
            url=url,
            title=title,
            source_crawler=source_crawler,
            processing_notes=processing_notes
        )

    def _extract_jina_content_from_string(self, jina_string: str) -> str:
        """Extract main content from Jina AI string response"""
        # Look for "Markdown Content:" section
        if "Markdown Content:" in jina_string:
            parts = jina_string.split("Markdown Content:")
            if len(parts) > 1:
                return parts[1].strip()

        # Look for content after metadata headers
        lines = jina_string.split('\n')
        content_start = 0

        for i, line in enumerate(lines):
            # Skip common Jina metadata lines
            if line.strip().startswith(('Title:', 'URL Source:', 'Published Time:', 'Warning:', 'Markdown Content:')):
                content_start = i + 1
                continue
            # Once we hit non-metadata, we're at the content
            elif content_start > 0 and line.strip():
                return '\n'.join(lines[content_start:])

        # Fallback: return everything after first empty line
        if '\n\n' in jina_string:
            return jina_string.split('\n\n', 1)[1].strip()

        return jina_string.strip()

    def _extract_jina_title_from_string(self, jina_string: str) -> str | None:
        """Extract title from Jina AI string response"""
        # Look for Title: line
        title_match = re.search(r'^Title:\s*(.+)$', jina_string, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()
            # Clean up title (remove URLs, dates, etc.)
            title = re.sub(r'\s*URL Source:.*$', '', title).strip()
            return title

        # Fallback: try to extract from first line if it looks like a title
        lines = jina_string.split('\n')
        if lines:
            first_line = lines[0].strip()
            # Remove common prefixes
            first_line = re.sub(r'^(Title:|URL Source:)\s*', '', first_line).strip()
            if len(first_line) < 200 and '\n' not in first_line:
                return first_line

        return None

    def _clean_jina_content(self, content: str) -> str:
        """Clean Jina-specific formatting and metadata"""
        # Remove Jina metadata lines
        lines = content.split('\n')
        cleaned_lines = []

        skip_next = False
        for line in lines:
            line_stripped = line.strip()

            # Skip metadata lines
            if line_stripped.startswith(('Title:', 'URL Source:', 'Published Time:', 'Warning:')):
                skip_next = line_stripped.startswith('Markdown Content:')
                continue

            # Skip the line after "Markdown Content:"
            if skip_next:
                skip_next = False
                continue

            # Clean up any remaining metadata
            if not any(line_stripped.startswith(prefix) for prefix in ['Title:', 'URL Source:', 'Published Time:']):
                cleaned_lines.append(line)

        content = '\n'.join(cleaned_lines).strip()

        # Additional cleaning
        content = re.sub(r'\[Learn more\]\(https://iana\.org/domains/example\)', '', content)  # Remove example.com link
        content = re.sub(r'\s*\n\s*', '\n', content)  # Normalize whitespace
        content = content.strip()

        return content

    def _clean_markdown_content(self, content: str) -> str:
        """Clean and normalize markdown content"""
        if not content:
            return ""

        # Normalize line endings
        content = content.replace('\r\n', '\n')

        # Remove excessive empty lines
        content = re.sub(r'\n{3,}', '\n\n', content)

        # Normalize spacing around headers
        content = re.sub(r'\n*(#{1,6}\s+)', r'\n\1', content)
        content = re.sub(r'(#{1,6}.+)\n*', r'\1\n\n', content)

        # Normalize list spacing
        content = re.sub(r'\n*(\s*[-*+]\s+)', r'\n\1', content)
        content = re.sub(r'\n*(\s*\d+\.\s+)', r'\n\1', content)

        # Trim whitespace
        content = content.strip()

        return content

    def get_normalization_stats(self) -> dict[str, Any]:
        """Get statistics about normalization performed"""
        return self.normalization_stats.copy()

    def reset_stats(self) -> None:
        """Reset normalization statistics"""
        self.normalization_stats = {
            "total_processed": 0,
            "jina_results": 0,
            "crawl4ai_results": 0,
            "normalizations_applied": 0
        }


# Convenience function for quick normalization
def normalize_crawl_result(raw_result: Any, source_crawler: str, url: str) -> NormalizedCrawlResult:
    """
    Quick normalization function

    Args:
        raw_result: Raw result from crawler
        source_crawler: Name of crawler ("jina_ai", "crawl4ai", etc.)
        url: Original URL

    Returns:
        NormalizedCrawlResult with consistent format
    """
    normalizer = CrawlResultNormalizer()
    return normalizer.normalize_result(raw_result, source_crawler, url)
