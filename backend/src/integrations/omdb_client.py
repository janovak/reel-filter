"""OMDb API client with retry logic, rate limiting, and error handling.

Fetches movie metadata from the OMDb API (https://www.omdbapi.com/).
Implements:
- Exponential backoff retry (2s, 4s, 8s) via tenacity
- Rate limiting (10 requests/second)
- Timeout handling (10 seconds)
- Response validation
"""
import os
import time
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

logger = logging.getLogger(__name__)

# Rate limiter: simple token bucket
_last_request_time: float = 0.0
_RATE_LIMIT_INTERVAL: float = 0.1  # 10 req/s = 100ms between requests


def _rate_limit():
    """Enforce rate limit of 10 requests/second."""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < _RATE_LIMIT_INTERVAL:
        time.sleep(_RATE_LIMIT_INTERVAL - elapsed)
    _last_request_time = time.time()


@dataclass
class OMDbMovie:
    """Parsed movie data from OMDb API response."""
    imdb_id: str
    title: str
    year: int
    runtime: Optional[int] = None
    genre: List[str] = field(default_factory=list)
    mpaa_rating: Optional[str] = None
    plot: Optional[str] = None
    director: Optional[str] = None
    cast: List[str] = field(default_factory=list)
    poster_url: Optional[str] = None
    imdb_rating: Optional[float] = None
    rt_rating: Optional[int] = None
    metacritic_rating: Optional[int] = None
    awards_summary: Optional[str] = None
    awards_count: int = 0
    nominations_count: int = 0


class OMDbClientError(Exception):
    """Base exception for OMDb client errors."""
    pass


class OMDbRateLimitError(OMDbClientError):
    """Raised when rate limit is exceeded."""
    pass


class OMDbNotFoundError(OMDbClientError):
    """Raised when movie is not found."""
    pass


class OMDbClient:
    """Client for the OMDb API with retry logic and rate limiting."""

    BASE_URL = "https://www.omdbapi.com/"
    TIMEOUT = 10.0  # seconds

    # Valid MPAA ratings
    VALID_MPAA = {'G', 'PG', 'PG-13', 'R', 'NC-17', 'Not Rated'}

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OMDB_API_KEY", "")
        if not self.api_key:
            logger.warning("OMDb API key not configured. Set OMDB_API_KEY environment variable.")
        self._client = httpx.Client(timeout=self.TIMEOUT)

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
    def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a rate-limited, retried request to OMDb API."""
        _rate_limit()
        params["apikey"] = self.api_key

        response = self._client.get(self.BASE_URL, params=params)
        response.raise_for_status()

        data = response.json()

        if data.get("Response") == "False":
            error_msg = data.get("Error", "Unknown error")
            if "not found" in error_msg.lower():
                raise OMDbNotFoundError(f"Movie not found: {error_msg}")
            if "request limit" in error_msg.lower():
                raise OMDbRateLimitError(f"Rate limit exceeded: {error_msg}")
            raise OMDbClientError(f"OMDb API error: {error_msg}")

        return data

    def search_by_title(self, title: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for movies by title. Returns list of search results."""
        params: Dict[str, Any] = {"s": title, "type": "movie"}
        if year:
            params["y"] = year

        try:
            data = self._make_request(params)
            return data.get("Search", [])
        except OMDbNotFoundError:
            return []

    def get_by_imdb_id(self, imdb_id: str) -> Optional[OMDbMovie]:
        """Get full movie details by IMDb ID."""
        try:
            data = self._make_request({"i": imdb_id, "plot": "full"})
            return self._parse_movie(data)
        except OMDbNotFoundError:
            return None
        except OMDbClientError as e:
            logger.error(f"Failed to fetch movie {imdb_id}: {e}")
            return None

    def get_by_title(self, title: str, year: Optional[int] = None) -> Optional[OMDbMovie]:
        """Get full movie details by title (and optional year)."""
        params: Dict[str, Any] = {"t": title, "type": "movie", "plot": "full"}
        if year:
            params["y"] = year

        try:
            data = self._make_request(params)
            return self._parse_movie(data)
        except OMDbNotFoundError:
            return None
        except OMDbClientError as e:
            logger.error(f"Failed to fetch movie '{title}': {e}")
            return None

    def _parse_movie(self, data: Dict[str, Any]) -> OMDbMovie:
        """Parse OMDb API response into OMDbMovie dataclass."""
        # Parse year
        year_str = data.get("Year", "0")
        try:
            year = int(year_str.split("–")[0].strip())  # Handle "2008–2013" format
        except (ValueError, IndexError):
            year = 0

        # Parse runtime
        runtime = None
        runtime_str = data.get("Runtime", "N/A")
        if runtime_str != "N/A":
            try:
                runtime = int(runtime_str.replace(" min", ""))
            except ValueError:
                pass

        # Parse genres
        genre_str = data.get("Genre", "")
        genres = [g.strip() for g in genre_str.split(",") if g.strip()] if genre_str != "N/A" else []

        # Parse MPAA rating
        mpaa = data.get("Rated", "Not Rated")
        mpaa_rating = mpaa if mpaa in self.VALID_MPAA else "Not Rated"

        # Parse cast
        cast_str = data.get("Actors", "")
        cast = [a.strip() for a in cast_str.split(",") if a.strip()] if cast_str != "N/A" else []

        # Parse IMDb rating
        imdb_rating = None
        try:
            val = data.get("imdbRating", "N/A")
            if val != "N/A":
                imdb_rating = float(val)
        except ValueError:
            pass

        # Parse Rotten Tomatoes from Ratings array
        rt_rating = None
        metacritic_rating = None
        for rating_obj in data.get("Ratings", []):
            source = rating_obj.get("Source", "")
            value = rating_obj.get("Value", "")
            if "Rotten Tomatoes" in source:
                try:
                    rt_rating = int(value.replace("%", ""))
                except ValueError:
                    pass
            elif "Metacritic" in source:
                try:
                    metacritic_rating = int(value.split("/")[0])
                except (ValueError, IndexError):
                    pass

        # Parse Metacritic from top-level if not in Ratings
        if metacritic_rating is None:
            try:
                mc_val = data.get("Metascore", "N/A")
                if mc_val != "N/A":
                    metacritic_rating = int(mc_val)
            except ValueError:
                pass

        # Parse awards
        awards_summary = data.get("Awards", None)
        if awards_summary == "N/A":
            awards_summary = None

        awards_count, nominations_count = self._parse_awards_counts(awards_summary)

        # Parse poster
        poster_url = data.get("Poster", None)
        if poster_url == "N/A":
            poster_url = None

        # Parse plot
        plot = data.get("Plot", None)
        if plot == "N/A":
            plot = None

        # Parse director
        director = data.get("Director", None)
        if director == "N/A":
            director = None

        return OMDbMovie(
            imdb_id=data.get("imdbID", ""),
            title=data.get("Title", ""),
            year=year,
            runtime=runtime,
            genre=genres,
            mpaa_rating=mpaa_rating,
            plot=plot,
            director=director,
            cast=cast,
            poster_url=poster_url,
            imdb_rating=imdb_rating,
            rt_rating=rt_rating,
            metacritic_rating=metacritic_rating,
            awards_summary=awards_summary,
            awards_count=awards_count,
            nominations_count=nominations_count,
        )

    @staticmethod
    def _parse_awards_counts(awards_text: Optional[str]) -> tuple:
        """Extract wins and nominations counts from awards summary text."""
        if not awards_text:
            return 0, 0

        import re
        wins = 0
        noms = 0

        # Match patterns like "42 wins" or "Won 4 Oscars"
        win_matches = re.findall(r'(\d+)\s*wins?', awards_text, re.IGNORECASE)
        won_matches = re.findall(r'Won\s+(\d+)', awards_text, re.IGNORECASE)
        nom_matches = re.findall(r'(\d+)\s*nomination', awards_text, re.IGNORECASE)
        nominated_matches = re.findall(r'Nominated\s+for\s+(\d+)', awards_text, re.IGNORECASE)

        for m in win_matches:
            wins += int(m)
        for m in won_matches:
            wins += int(m)
        for m in nom_matches:
            noms += int(m)
        for m in nominated_matches:
            noms += int(m)

        return wins, noms
