from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ai_studio",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    timezone="UTC",
)

celery_app.autodiscover_tasks(["app.workers"])

import app.services.trainers
import app.workers.tasks