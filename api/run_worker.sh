./sanity_checks.sh
celery -A celery_task_app.worker worker --loglevel=info --logfile=celery.log --concurrency=1