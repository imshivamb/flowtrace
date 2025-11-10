from celery import Celery
from app.core.config import settings

celery = Celery(
    "workflow-engine",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

@celery.task
def execute_workflow(run_id: str)
    # Filling it soon
    return f"executed {run_id}"