"""Scheduled data refresh tasks.

Thin Celery wrappers around src/services/data_pipeline.py — the same
scrape_kim()/fetch_omdb() functions the manual CLI (scripts/manual_refresh.py)
calls, so the scheduled and on-demand paths can't drift apart.

Schedule (see celery_app.py):
- OMDb enrichment: daily, quota-aware (OMDb free tier caps at 1,000/day, so a
  large initial backlog is cleared over several days automatically).
- KIM re-crawl: weekly. Existing scores are cheap to overwrite at this volume,
  so this stays a full 26-page scan rather than an incremental one — the main
  purpose is picking up newly added movies.
"""
import logging

from src.jobs.celery_app import celery_app
from src.services.data_pipeline import scrape_kim, fetch_omdb

logger = logging.getLogger(__name__)

# Stay under OMDb's free-tier daily quota (1,000 requests/day)
OMDB_DAILY_LIMIT = 900


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="src.jobs.weekly_refresh.refresh_omdb_data",
)
def refresh_omdb_data(self, limit: int = OMDB_DAILY_LIMIT):
    try:
        return fetch_omdb(limit=limit)
    except Exception as exc:
        logger.error(f"OMDb refresh failed: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="src.jobs.weekly_refresh.refresh_kim_data",
)
def refresh_kim_data(self):
    try:
        return scrape_kim()
    except Exception as exc:
        logger.error(f"KIM refresh failed: {exc}")
        raise self.retry(exc=exc)
