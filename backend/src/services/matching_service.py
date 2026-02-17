"""Fuzzy matching service using RapidFuzz.

Matches movie titles from OMDb API to Kids-in-Mind scraped entries.
Thresholds:
- >88% confidence: auto-match
- 75-88% confidence: manual review queue
- <75% confidence: no match (skip)
"""
import logging
from typing import Optional, List, Tuple
from dataclasses import dataclass
import re

from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """Result of fuzzy matching between two movie titles."""
    omdb_title: str
    omdb_year: Optional[int]
    kim_title: str
    kim_year: Optional[int]
    confidence: float
    auto_matched: bool  # True if >88%, False if 75-88% (needs review)
    kim_url: Optional[str] = None

    @property
    def needs_review(self) -> bool:
        """Match is in the manual review range (75-88%)."""
        return 75.0 <= self.confidence <= 88.0


# Thresholds
AUTO_MATCH_THRESHOLD = 88.0
REVIEW_THRESHOLD = 75.0
SKIP_THRESHOLD = 75.0  # Below this, don't match at all


def normalize_title(title: str) -> str:
    """Normalize a movie title for better fuzzy matching.

    Removes common prefixes/suffixes, articles, and special characters.
    """
    if not title:
        return ""

    # Convert to lowercase
    t = title.lower().strip()

    # Remove year in parentheses
    t = re.sub(r'\s*\(\d{4}\)\s*', '', t)

    # Remove leading articles
    t = re.sub(r'^(the|a|an)\s+', '', t)

    # Remove special characters but keep spaces
    t = re.sub(r'[^\w\s]', '', t)

    # Collapse whitespace
    t = re.sub(r'\s+', ' ', t).strip()

    return t


class MatchingService:
    """Service for fuzzy matching movie titles between data sources."""

    def __init__(
        self,
        auto_threshold: float = AUTO_MATCH_THRESHOLD,
        review_threshold: float = REVIEW_THRESHOLD,
    ):
        self.auto_threshold = auto_threshold
        self.review_threshold = review_threshold

    def match_single(
        self,
        omdb_title: str,
        omdb_year: Optional[int],
        kim_entries: List[dict],
    ) -> Optional[MatchResult]:
        """
        Match a single OMDb movie to the best KIM entry.

        Args:
            omdb_title: Movie title from OMDb
            omdb_year: Release year from OMDb
            kim_entries: List of dicts with 'title', 'year' (optional), 'url' (optional)

        Returns:
            MatchResult if confidence >= review_threshold, None otherwise
        """
        if not kim_entries:
            return None

        normalized_omdb = normalize_title(omdb_title)

        # Build list of (normalized_title, index) for matching
        kim_titles_normalized = []
        for i, entry in enumerate(kim_entries):
            kim_titles_normalized.append((normalize_title(entry.get("title", "")), i))

        # Use RapidFuzz to find best match using weighted ratio
        best_match = None
        best_score = 0.0
        best_idx = -1

        for norm_title, idx in kim_titles_normalized:
            if not norm_title:
                continue

            # Use token_sort_ratio for resilience to word order differences
            score = fuzz.token_sort_ratio(normalized_omdb, norm_title)

            # Boost score if years match
            kim_year = kim_entries[idx].get("year")
            if omdb_year and kim_year and omdb_year == kim_year:
                score = min(100.0, score + 5.0)  # Year match bonus
            elif omdb_year and kim_year and abs(omdb_year - kim_year) > 1:
                score = max(0.0, score - 10.0)  # Year mismatch penalty

            if score > best_score:
                best_score = score
                best_idx = idx
                best_match = kim_entries[idx]

        if best_match is None or best_score < self.review_threshold:
            return None

        return MatchResult(
            omdb_title=omdb_title,
            omdb_year=omdb_year,
            kim_title=best_match.get("title", ""),
            kim_year=best_match.get("year"),
            confidence=round(best_score, 2),
            auto_matched=best_score > self.auto_threshold,
            kim_url=best_match.get("url"),
        )

    def match_batch(
        self,
        omdb_movies: List[dict],
        kim_entries: List[dict],
    ) -> Tuple[List[MatchResult], List[MatchResult], List[dict]]:
        """
        Match a batch of OMDb movies to KIM entries.

        Returns:
            Tuple of (auto_matched, needs_review, unmatched)
        """
        auto_matched = []
        needs_review = []
        unmatched = []

        for movie in omdb_movies:
            title = movie.get("title", "")
            year = movie.get("year")

            result = self.match_single(title, year, kim_entries)

            if result is None:
                unmatched.append(movie)
            elif result.auto_matched:
                auto_matched.append(result)
            else:
                needs_review.append(result)

        logger.info(
            f"Matching results: {len(auto_matched)} auto-matched, "
            f"{len(needs_review)} need review, {len(unmatched)} unmatched"
        )

        return auto_matched, needs_review, unmatched

    @staticmethod
    def get_review_queue(
        review_matches: List[MatchResult],
    ) -> List[dict]:
        """
        Format matches needing review into a queue for manual verification.

        Returns list of dicts with match details for human review.
        """
        queue = []
        for match in sorted(review_matches, key=lambda m: m.confidence, reverse=True):
            queue.append({
                "omdb_title": match.omdb_title,
                "omdb_year": match.omdb_year,
                "kim_title": match.kim_title,
                "kim_year": match.kim_year,
                "confidence": match.confidence,
                "kim_url": match.kim_url,
                "action": "pending",  # pending, approve, reject
            })
        return queue
