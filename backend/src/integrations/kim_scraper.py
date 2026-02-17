"""Kids-in-Mind web scraper with BeautifulSoup4.

Scrapes content ratings (sex/nudity, violence/gore, language/profanity)
from Kids-in-Mind (https://kids-in-mind.com/).

Implements:
- Rate limiting (0.5 requests/second to be respectful)
- Content score validation (0-10 range)
- Error handling with detailed logging
- Retry logic for transient failures
"""
import re
import time
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

logger = logging.getLogger(__name__)

# Rate limiter: 0.5 req/s = 2 seconds between requests
_last_scrape_time: float = 0.0
_SCRAPE_INTERVAL: float = 2.0


def _scrape_rate_limit():
    """Enforce rate limit of 0.5 requests/second."""
    global _last_scrape_time
    now = time.time()
    elapsed = now - _last_scrape_time
    if elapsed < _SCRAPE_INTERVAL:
        time.sleep(_SCRAPE_INTERVAL - elapsed)
    _last_scrape_time = time.time()


@dataclass
class KIMContentScore:
    """Parsed content scores from Kids-in-Mind."""
    title: str
    sex_nudity: int
    violence_gore: int
    language_profanity: int
    year: Optional[int] = None
    kim_url: Optional[str] = None


class KIMScraperError(Exception):
    """Base exception for KIM scraper errors."""
    pass


class KIMParsingError(KIMScraperError):
    """Raised when content scores cannot be parsed from page."""
    pass


def validate_content_score(score: int, field_name: str) -> int:
    """Validate that a content score is in the 0-10 range."""
    if not isinstance(score, int):
        raise ValueError(f"{field_name} must be an integer, got {type(score)}")
    if score < 0 or score > 10:
        raise ValueError(f"{field_name} must be between 0 and 10, got {score}")
    return score


class KIMScraper:
    """Scraper for Kids-in-Mind content ratings."""

    BASE_URL = "https://kids-in-mind.com"
    TIMEOUT = 15.0  # seconds (KIM can be slow)
    USER_AGENT = (
        "Mozilla/5.0 (compatible; Reel-Filter/1.0; "
        "+https://github.com/reel-filter/reel-filter)"
    )

    def __init__(self):
        self._client = httpx.Client(
            timeout=self.TIMEOUT,
            headers={"User-Agent": self.USER_AGENT},
            follow_redirects=True,
        )

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def _fetch_page(self, url: str) -> str:
        """Fetch a page with rate limiting and retry."""
        _scrape_rate_limit()
        response = self._client.get(url)
        response.raise_for_status()
        return response.text

    def get_movie_list(self, page: int = 1) -> List[Dict[str, Any]]:
        """
        Get list of movies from KIM index pages.
        Returns list of dicts with title, url, and scores if available.
        """
        results = []
        try:
            # KIM lists movies alphabetically and by rating
            url = f"{self.BASE_URL}/search.php?p={page}"
            html = self._fetch_page(url)
            soup = BeautifulSoup(html, "lxml")

            # Parse movie listings from search/index pages
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                text = link.get_text(strip=True)
                if href and text and ("/movie/" in href or re.match(r'.*\d+\.htm', href)):
                    movie_url = href if href.startswith("http") else f"{self.BASE_URL}/{href.lstrip('/')}"
                    results.append({
                        "title": text,
                        "url": movie_url,
                    })

        except Exception as e:
            logger.error(f"Failed to fetch KIM movie list page {page}: {e}")

        return results

    def scrape_movie_scores(self, url: str) -> Optional[KIMContentScore]:
        """
        Scrape content scores from a specific KIM movie page.

        Kids-in-Mind pages typically show scores as:
        "SEX/NUDITY 3 | VIOLENCE/GORE 8 | LANGUAGE 5"
        or similar patterns with the three category scores.
        """
        try:
            html = self._fetch_page(url)
            return self._parse_scores(html, url)
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error scraping {url}: {e.response.status_code}")
            return None
        except KIMParsingError as e:
            logger.warning(f"Parsing error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}")
            return None

    def _parse_scores(self, html: str, url: str) -> KIMContentScore:
        """Parse content scores from KIM HTML page."""
        soup = BeautifulSoup(html, "lxml")

        # Get the page text for score extraction
        text = soup.get_text(separator=" ")

        # Try multiple patterns for score extraction
        scores = self._extract_scores_from_text(text)

        if scores is None:
            # Try parsing from structured elements
            scores = self._extract_scores_from_elements(soup)

        if scores is None:
            raise KIMParsingError(f"Could not extract content scores from {url}")

        sex, violence, language = scores

        # Validate scores
        sex = validate_content_score(sex, "sex_nudity")
        violence = validate_content_score(violence, "violence_gore")
        language = validate_content_score(language, "language_profanity")

        # Extract title
        title = ""
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)
            # Clean up title (remove " - Kids-in-Mind.com" suffix)
            title = re.sub(r'\s*[-–|]\s*Kids.*$', '', title, flags=re.IGNORECASE).strip()

        # Try to extract year from title or page
        year = None
        year_match = re.search(r'\((\d{4})\)', title)
        if year_match:
            year = int(year_match.group(1))
            title = re.sub(r'\s*\(\d{4}\)\s*', '', title).strip()

        return KIMContentScore(
            title=title,
            sex_nudity=sex,
            violence_gore=violence,
            language_profanity=language,
            year=year,
            kim_url=url,
        )

    def _extract_scores_from_text(self, text: str) -> Optional[tuple]:
        """Extract scores from page text using regex patterns."""
        # Pattern: "SEX/NUDITY X" ... "VIOLENCE/GORE Y" ... "LANGUAGE Z"
        # or "SEX & NUDITY: X" etc.
        patterns = [
            # Pattern 1: "SEX/NUDITY 3 | VIOLENCE/GORE 8 | LANGUAGE 5"
            r'SEX[/&\s]+NUDITY\s*[:=]?\s*(\d{1,2}).*?VIOLENCE[/&\s]+GORE\s*[:=]?\s*(\d{1,2}).*?LANGUAGE\s*[:=]?\s*(\d{1,2})',
            # Pattern 2: individual scores
            r'SEX[/&\s]+NUDITY\s*[:=]?\s*(\d{1,2})',
        ]

        # Try the full pattern first
        match = re.search(patterns[0], text, re.IGNORECASE | re.DOTALL)
        if match:
            return (int(match.group(1)), int(match.group(2)), int(match.group(3)))

        # Try individual patterns
        sex_match = re.search(r'SEX[/&\s]+NUDITY\s*[:=]?\s*(\d{1,2})', text, re.IGNORECASE)
        violence_match = re.search(r'VIOLENCE[/&\s]+GORE\s*[:=]?\s*(\d{1,2})', text, re.IGNORECASE)
        language_match = re.search(r'(?:LANGUAGE|PROFANITY)\s*[:=]?\s*(\d{1,2})', text, re.IGNORECASE)

        if sex_match and violence_match and language_match:
            return (
                int(sex_match.group(1)),
                int(violence_match.group(1)),
                int(language_match.group(1)),
            )

        return None

    def _extract_scores_from_elements(self, soup: BeautifulSoup) -> Optional[tuple]:
        """Try to extract scores from specific HTML elements."""
        # Look for score elements in common KIM page structures
        score_elements = soup.find_all(
            class_=re.compile(r'score|rating|content[-_]?level', re.IGNORECASE)
        )

        scores = []
        for elem in score_elements:
            text = elem.get_text(strip=True)
            match = re.search(r'(\d{1,2})', text)
            if match:
                val = int(match.group(1))
                if 0 <= val <= 10:
                    scores.append(val)

        if len(scores) >= 3:
            return (scores[0], scores[1], scores[2])

        return None
