import os
import time

from celery import Celery


app = Celery(
    "celery_app",
    broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379"),
    backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379"),
    include=["celery_task_app.tasks"],
)
