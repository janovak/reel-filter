"""Celery application configuration with Beat schedule.

Configures Celery for:
- Redis as broker and result backend
- Weekly data refresh task (Sunday 2 AM)
- Retry policies for failed tasks
"""
import os
from celery import Celery
from celery.schedules import crontab

# Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "reel_filter",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["src.jobs.weekly_refresh"],
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task settings
    task_acks_late=True,  # Acknowledge after task completion (for reliability)
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,  # Only fetch one task at a time

    # Retry defaults
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,

    # Result expiry
    result_expires=86400,  # 24 hours

    # Beat schedule - weekly data refresh
    beat_schedule={
        "weekly-omdb-refresh": {
            "task": "src.jobs.weekly_refresh.refresh_omdb_data",
            "schedule": crontab(
                hour=2,
                minute=0,
                day_of_week="sunday",
            ),
            "kwargs": {},
            "options": {"queue": "default"},
        },
        "weekly-kim-refresh": {
            "task": "src.jobs.weekly_refresh.refresh_kim_data",
            "schedule": crontab(
                hour=3,
                minute=0,
                day_of_week="sunday",
            ),
            "kwargs": {},
            "options": {"queue": "default"},
        },
    },
)
