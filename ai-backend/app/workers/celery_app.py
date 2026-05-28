"""
LabMind AI — Celery Application
Shared Celery instance used by all background workers.
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "labmind",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks_analysis"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # 1 task at a time (analysis is heavy)
)

# Autodiscover tasks in app.workers
# NOTE: autodiscover_tasks looks for `tasks.py` by convention.
# Our tasks live in `tasks_analysis.py`, so we must explicitly include them.
celery_app.autodiscover_tasks(["app.workers"], related_name="tasks_analysis")
